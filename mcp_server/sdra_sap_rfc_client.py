import os
from typing import Any, Dict


class SdraSapRfcClient:
    """RFC client wrapper for SDRA SAP function modules."""

    def __init__(self):
        try:
            from pyrfc import Connection
        except ImportError as exc:
            raise RuntimeError(
                "pyrfc is not installed. Install SAP NetWeaver RFC SDK first, then run: "
                "python -m pip install pyrfc"
            ) from exc

        self.conn = Connection(
            ashost=self._env("SDRA_SAP_ASHOST"),
            sysnr=self._env("SDRA_SAP_SYSNR"),
            client=self._env("SDRA_SAP_CLIENT"),
            user=self._env("SDRA_SAP_USERNAME"),
            passwd=self._env("SDRA_SAP_PASSWORD"),
            lang=os.environ.get("SDRA_SAP_LANG", "EN"),
        )

    @staticmethod
    def required_env() -> list[str]:
        return [
            "SDRA_SAP_ASHOST",
            "SDRA_SAP_SYSNR",
            "SDRA_SAP_CLIENT",
            "SDRA_SAP_USERNAME",
            "SDRA_SAP_PASSWORD",
        ]

    @classmethod
    def missing_env(cls) -> list[str]:
        return [name for name in cls.required_env() if not os.environ.get(name)]

    def create_approval_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.conn.call(
            "Z_SDRA_CREATE_APPR_REQ",
            IV_APPROVAL_TYPE=payload["approval_type"],
            IV_SALES_ORDER=payload["sales_order"],
            IV_SALES_ORDER_ITEM=payload["sales_order_item"],
            IV_DISPATCH_QTY=payload["dispatch_qty"],
            IV_UOM=payload["uom"],
            IV_READINESS_STATUS=payload["readiness_status"],
            IV_REASON_CODE=payload["reason_code"],
            IV_OWNER_TEAM=payload["owner_team"],
        )

    def write_action_log(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.conn.call(
            "Z_SDRA_WRITE_ACT_LOG",
            IV_RUN_ID=payload.get("run_id", ""),
            IV_EVENT_NAME=payload["event_name"],
            IV_ACTION_NAME=payload["action_name"],
            IV_VBELN=payload.get("sales_order", ""),
            IV_POSNR=payload.get("sales_order_item", ""),
            IV_STATUS=payload["status"],
            IV_MESSAGE=payload["message"],
        )

    def create_outbound_delivery(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action_mode = os.environ.get("SDRA_ACTION_MODE", "APPROVAL_ONLY")
        if action_mode != "CONTROLLED_AUTONOMY":
            return {
                "EV_STATUS": "SKIPPED_APPROVAL_REQUIRED",
                "EV_DELIVERY": "",
                "EV_MESSAGE": "Outbound delivery creation is blocked because SDRA_ACTION_MODE is not CONTROLLED_AUTONOMY",
            }

        return self.conn.call(
            "Z_SDRA_CREATE_DELIVERY",
            IV_APPROVAL_ID=payload["approval_id"],
            IV_SALES_ORDER=payload["sales_order"],
            IV_SALES_ORDER_ITEM=payload["sales_order_item"],
            IV_DELIVERY_QTY=payload["delivery_qty"],
            IV_UOM=payload["uom"],
        )

    def _env(self, name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

