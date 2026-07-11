import json

from sdra_mcp_server import handle_request


def main():
    response = handle_request({
        "tool": "sdra_check_sap_config",
        "payload": {},
    })
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()

