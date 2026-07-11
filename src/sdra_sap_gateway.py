import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sdra_models import SdraActionResult, SdraDecision


class SdraSapGateway:
    object_name = "SDRA_SAP_GATEWAY"

    def __init__(self, config: Dict[str, Any], base_dir: Path):
        self.config = config
        self.base_dir = base_dir
        self.connection = config["sap_connection"]
        self.services = config["sap_services"]
        self.runtime = config["runtime"]
        self.base_url = self._env(self.connection["base_url_env"], required=False)
        self.sap_client = self._env(self.connection["client_env"], required=False)
        self.auth_mode = self._env(self.connection["auth_mode_env"], required=False) or "BASIC"
        self.timeout = int(self.connection.get("timeout_seconds", 30))
        self.action_mode = self._env(self.runtime["action_mode_env"], required=False) or self.runtime["default_action_mode"]

    def validate_connection_settings(self) -> List[str]:
        missing = []
        for key in ("base_url_env", "client_env"):
            env_name = self.connection[key]
            if not os.environ.get(env_name):
                missing.append(env_name)
        if self.auth_mode == "BASIC":
            for key in ("username_env", "password_env"):
                env_name = self.connection[key]
                if not os.environ.get(env_name):
                    missing.append(env_name)
        if self.auth_mode == "BEARER" and not os.environ.get(self.connection["bearer_token_env"]):
            missing.append(self.connection["bearer_token_env"])
        return missing

    def fetch_open_sales_orders(self, planning_date: str, horizon_days: int) -> List[Dict[str, Any]]:
        params = {
            "$top": "50",
        }
        return self._get_collection(self.services["open_sales_orders_path"], params)

    def create_approval_request(self, decision: SdraDecision) -> SdraActionResult:
        payload = {
            "ApprovalType": self._approval_type(decision),
            "SalesOrder": decision.order.sales_order,
            "SalesOrderItem": decision.order.sales_order_item,
            "DispatchQty": str(decision.dispatch_qty),
            "Uom": decision.order.sales_unit or "EA",
            "ReadinessStatus": decision.readiness_status,
            "ReasonCode": decision.reason_code,
            "OwnerTeam": decision.owner_team,
        }
        return self._post_action("SDRA_ACTION_REQUEST_DELIVERY_APPROVAL", self.services["approval_request_path"], payload)

    def create_outbound_delivery(self, decision: SdraDecision) -> SdraActionResult:
        if self.action_mode != "CONTROLLED_AUTONOMY":
            return SdraActionResult(
                action_name="SDRA_ACTION_CREATE_OUTBOUND_DELIVERY",
                status="SKIPPED_APPROVAL_REQUIRED",
                sap_document="",
                message="Outbound delivery creation is blocked because SDRA_ACTION_MODE is not CONTROLLED_AUTONOMY",
            )
        payload = {
            "sales_order": decision.order.sales_order,
            "sales_order_item": decision.order.sales_order_item,
            "delivery_qty": decision.dispatch_qty,
            "plant": decision.order.plant,
            "shipping_point": decision.order.shipping_point,
        }
        return self._post_action("SDRA_ACTION_CREATE_OUTBOUND_DELIVERY", self.services["create_delivery_path"], payload)

    def escalate_blocked_order(self, decision: SdraDecision) -> SdraActionResult:
        payload = {
            "sales_order": decision.order.sales_order,
            "sales_order_item": decision.order.sales_order_item,
            "reason_code": decision.reason_code,
            "owner_team": decision.owner_team,
            "message": f"{decision.readiness_status}: {decision.reason_code}",
        }
        self.write_action_log("SDRA_ACTION_ESCALATE_BLOCKED_ORDER", payload)
        return SdraActionResult("SDRA_ACTION_ESCALATE_BLOCKED_ORDER", "LOGGED", "", "Escalation logged")

    def monitor_delivery(self, decision: SdraDecision) -> SdraActionResult:
        payload = {
            "sales_order": decision.order.sales_order,
            "sales_order_item": decision.order.sales_order_item,
            "reason_code": decision.reason_code,
        }
        self.write_action_log("SDRA_ACTION_MONITOR_PGI_STATUS", payload)
        return SdraActionResult("SDRA_ACTION_MONITOR_PGI_STATUS", "LOGGED", "", "Monitor action logged")

    def write_action_log(self, event_name: str, payload: Dict[str, Any]) -> None:
        log_payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "agent": "SDRA_DISPATCH_READINESS_AGENT",
            "event_name": event_name,
            "payload": payload,
        }
        action_log_path = self.services.get("action_log_path")
        if action_log_path and self.base_url:
            try:
                self._post_json(action_log_path, log_payload)
                return
            except Exception:
                pass
        local_log = self.base_dir / self.runtime["local_runtime_log"]
        local_log.parent.mkdir(parents=True, exist_ok=True)
        with local_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(log_payload) + "\n")

    def _get_collection(self, path: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        response = self._request_json("GET", path, params=params)
        if isinstance(response, dict) and "d" in response and "results" in response["d"]:
            return response["d"]["results"]
        if isinstance(response, dict) and "value" in response:
            return response["value"]
        if isinstance(response, list):
            return response
        return []

    def _post_action(self, action_name: str, path: str, payload: Dict[str, Any]) -> SdraActionResult:
        try:
            response = self._post_json(path, payload)
            data = response.get("d", response) if isinstance(response, dict) else {}
            sap_document = str(data.get("ApprovalId") or data.get("sap_document") or data.get("DeliveryDocument") or "")
            status = str(data.get("Status") or "SUCCESS")
            message = str(data.get("Message") or "SAP action completed")
            return SdraActionResult(action_name, status, sap_document, message)
        except HTTPError as exc:
            return SdraActionResult(action_name, "FAILED", "", f"SAP HTTP error {exc.code}")
        except Exception as exc:
            return SdraActionResult(action_name, "FAILED", "", str(exc))

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request_json("POST", path, body=payload)

    def _request_json(self, method: str, path: str, params: Dict[str, str] = None, body: Dict[str, Any] = None) -> Any:
        if not self.base_url:
            raise RuntimeError("SDRA_SAP_BASE_URL is not configured")
        query = ""
        merged_params = dict(params or {})
        if self.sap_client:
            merged_params["sap-client"] = self.sap_client
        if merged_params:
            query = "?" + urlencode(merged_params)
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/") + query
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(url, data=data, method=method)
        request.add_header("Accept", "application/json")
        request.add_header("Content-Type", "application/json")
        for header, value in self._auth_headers().items():
            request.add_header(header, value)
        with urlopen(request, timeout=self.timeout) as response:
            text = response.read().decode("utf-8")
        return json.loads(text) if text else {}

    def _auth_headers(self) -> Dict[str, str]:
        if self.auth_mode == "BEARER":
            return {"Authorization": f"Bearer {self._env(self.connection['bearer_token_env'])}"}
        if self.auth_mode == "BASIC":
            username = self._env(self.connection["username_env"])
            password = self._env(self.connection["password_env"])
            token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {token}"}
        return {}

    def _env(self, name: str, required: bool = True) -> str:
        value = os.environ.get(name, "")
        if required and not value:
            raise RuntimeError(f"Missing environment variable: {name}")
        return value

    def _approval_type(self, decision: SdraDecision) -> str:
        if decision.readiness_status == "PARTIALLY_READY":
            return "SDRA_APPR_CREATE_PARTIAL_DELIVERY"
        return "SDRA_APPR_CREATE_FULL_DELIVERY"
