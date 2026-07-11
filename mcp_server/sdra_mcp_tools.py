from typing import Any, Dict

from sdra_sap_rfc_client import SdraSapRfcClient


def sdra_check_sap_config(_: Dict[str, Any] | None = None) -> Dict[str, Any]:
    missing = SdraSapRfcClient.missing_env()
    return {
        "ok": not missing,
        "missing_environment_variables": missing,
        "message": "SAP RFC configuration is ready" if not missing else "SAP RFC configuration is incomplete",
    }


def sdra_create_approval_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = SdraSapRfcClient()
    return client.create_approval_request(payload)


def sdra_write_action_log(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = SdraSapRfcClient()
    return client.write_action_log(payload)


def sdra_create_outbound_delivery(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = SdraSapRfcClient()
    return client.create_outbound_delivery(payload)


TOOLS = {
    "sdra_check_sap_config": sdra_check_sap_config,
    "sdra_create_approval_request": sdra_create_approval_request,
    "sdra_write_action_log": sdra_write_action_log,
    "sdra_create_outbound_delivery": sdra_create_outbound_delivery,
}

