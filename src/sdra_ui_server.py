import json
import os
import sys
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdra_agentic_core import SdraDispatchReadinessAgent
from sdra_readiness_engine import SdraReadinessEngine
from sdra_run_sap_agent import load_config, resolve_planning_date
from sdra_sap_gateway import SdraSapGateway


SDRA_UI_OBJECT_NAME = "SDRA_DISPATCH_READINESS_AGENT_UI"


class SdraUiServer(BaseHTTPRequestHandler):
    base_dir = Path(__file__).resolve().parents[1]
    ui_dir = base_dir / "ui"
    config_path = base_dir / "config" / "sdra_agent_config.example.json"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_file(self.ui_dir / "index.html", "text/html")
            return
        if parsed.path == "/api/status":
            self._send_json(self._status_payload())
            return
        if parsed.path == "/api/config":
            self._send_json(load_config(self.config_path))
            return
        if parsed.path.startswith("/ui/"):
            relative = parsed.path.replace("/ui/", "", 1)
            target = (self.ui_dir / relative).resolve()
            if self.ui_dir.resolve() in target.parents or target == self.ui_dir.resolve():
                self._send_file(target, self._content_type(target))
                return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/check-config":
            body = self._read_json_body()
            self._send_json(self._check_config_payload(body))
            return
        if parsed.path == "/api/run":
            body = self._read_json_body()
            self._send_json(self._run_agent(body))
            return
        self._send_json({"error": "Not found"}, status=404)

    def _status_payload(self):
        config = load_config(self.config_path)
        gateway = SdraSapGateway(config, self.base_dir)
        missing = gateway.validate_connection_settings()
        return {
            "object_name": SDRA_UI_OBJECT_NAME,
            "agent_object": "SDRA_DISPATCH_READINESS_AGENT",
            "status": "READY" if not missing else "MISSING_CONFIG",
            "missing_environment_variables": missing,
            "action_mode": os.environ.get("SDRA_ACTION_MODE", config["runtime"]["default_action_mode"]),
            "sap_base_url_configured": bool(os.environ.get("SDRA_SAP_BASE_URL")),
            "sap_client_configured": bool(os.environ.get("SDRA_SAP_CLIENT")),
            "auth_mode": os.environ.get("SDRA_SAP_AUTH_MODE", "BASIC"),
        }

    def _run_agent(self, body):
        config = load_config(self.config_path)
        planning_date_value = body.get("planning_date") or "TODAY"
        horizon_days = int(config["runtime"].get("planning_horizon_days", 0))
        env_values = self._runtime_env(body)

        with temporary_environment(env_values):
            gateway = SdraSapGateway(config, self.base_dir)
            missing = gateway.validate_connection_settings()
            if missing:
                return {
                    "ok": False,
                    "status": "MISSING_CONFIG",
                    "message": "SAP connection settings are incomplete.",
                    "missing_environment_variables": missing,
                }
            planning_date = resolve_planning_date(planning_date_value)
            agent = SdraDispatchReadinessAgent(gateway, SdraReadinessEngine())
            try:
                result = agent.run(planning_date, horizon_days)
                return {"ok": True, "status": "COMPLETED", "result": result}
            except Exception as exc:
                return {
                    "ok": False,
                    "status": "SAP_CALL_FAILED",
                    "message": str(exc),
                }

    def _check_config_payload(self, body):
        config = load_config(self.config_path)
        env_values = self._runtime_env(body)
        with temporary_environment(env_values):
            gateway = SdraSapGateway(config, self.base_dir)
            missing = gateway.validate_connection_settings()
            return {
                "object_name": SDRA_UI_OBJECT_NAME,
                "agent_object": "SDRA_DISPATCH_READINESS_AGENT",
                "status": "READY" if not missing else "MISSING_CONFIG",
                "missing_environment_variables": missing,
                "action_mode": os.environ.get("SDRA_ACTION_MODE", config["runtime"]["default_action_mode"]),
                "sap_base_url_configured": bool(os.environ.get("SDRA_SAP_BASE_URL")),
                "sap_client_configured": bool(os.environ.get("SDRA_SAP_CLIENT")),
                "auth_mode": os.environ.get("SDRA_SAP_AUTH_MODE", "BASIC"),
                "message": "SAP runtime configuration is available." if not missing else "SAP connection settings are incomplete.",
            }

    def _runtime_env(self, body):
        mapped = {
            "SDRA_SAP_BASE_URL": body.get("sap_base_url", ""),
            "SDRA_SAP_CLIENT": body.get("sap_client", ""),
            "SDRA_SAP_AUTH_MODE": body.get("auth_mode", ""),
            "SDRA_SAP_USERNAME": body.get("sap_username", ""),
            "SDRA_SAP_PASSWORD": body.get("sap_password", ""),
            "SDRA_SAP_BEARER_TOKEN": body.get("sap_bearer_token", ""),
            "SDRA_ACTION_MODE": body.get("action_mode", ""),
        }
        return {key: value for key, value in mapped.items() if value}

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw)

    def _send_file(self, path, content_type):
        if not path.exists() or not path.is_file():
            self._send_json({"error": "File not found"}, status=404)
            return
        payload = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _content_type(self, path):
        suffix = path.suffix.lower()
        if suffix == ".css":
            return "text/css"
        if suffix == ".js":
            return "application/javascript"
        if suffix == ".svg":
            return "image/svg+xml"
        return "application/octet-stream"

    def log_message(self, format, *args):
        return


@contextmanager
def temporary_environment(values):
    original = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main():
    port = int(os.environ.get("SDRA_UI_PORT", "8010"))
    server = ThreadingHTTPServer(("127.0.0.1", port), SdraUiServer)
    print(f"{SDRA_UI_OBJECT_NAME} running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
