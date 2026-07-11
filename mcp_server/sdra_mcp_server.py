import json
import sys
from typing import Any, Dict

from sdra_mcp_tools import TOOLS


SERVER_NAME = "sdra-sap-mcp-server"


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Tiny JSON-line tool dispatcher.

    This file is intentionally dependency-light. If your MCP runtime already has
    a preferred Python SDK, keep the tool names and payloads, then wire these
    functions into that SDK's server object.
    """
    tool_name = request.get("tool")
    payload = request.get("payload") or {}

    if tool_name not in TOOLS:
        return {
            "ok": False,
            "server": SERVER_NAME,
            "error": f"Unknown SDRA tool: {tool_name}",
            "available_tools": sorted(TOOLS),
        }

    try:
        result = TOOLS[tool_name](payload)
        return {
            "ok": True,
            "server": SERVER_NAME,
            "tool": tool_name,
            "result": result,
        }
    except Exception as exc:
        return {
            "ok": False,
            "server": SERVER_NAME,
            "tool": tool_name,
            "error": str(exc),
        }


def main() -> int:
    print(json.dumps({
        "server": SERVER_NAME,
        "status": "started",
        "tools": sorted(TOOLS),
    }), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
        except Exception as exc:
            response = {
                "ok": False,
                "server": SERVER_NAME,
                "error": str(exc),
            }
        print(json.dumps(response), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

