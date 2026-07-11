# SDRA SAP MCP Server

## MCP Server Name

`sdra-sap-mcp-server`

## Purpose

Expose SAP RFC-enabled SDRA function modules as agent tools.

Flow:

```text
Agent / UI
  -> MCP tool
  -> Python RFC client
  -> SAP RFC-enabled function module
  -> ZSDRA_* table / delivery wrapper
```

## SAP RFC Function Modules Required

These must be active and remote-enabled in SAP:

```text
Z_SDRA_CREATE_APPR_REQ
Z_SDRA_WRITE_ACT_LOG
Z_SDRA_CREATE_DELIVERY
```

All import/export parameters must be **Pass Value**.

## Python Dependency

This server requires SAP NetWeaver RFC SDK and Python package:

```bash
pyrfc
```

Install only after SAP NW RFC SDK is configured:

```bash
python -m pip install pyrfc
```

## Environment Variables

Git Bash:

```bash
export SDRA_SAP_ASHOST="your.sap.host"
export SDRA_SAP_SYSNR="00"
export SDRA_SAP_CLIENT="100"
export SDRA_SAP_USERNAME="your_user"
export SDRA_SAP_PASSWORD="your_password"
export SDRA_SAP_LANG="EN"
export SDRA_ACTION_MODE="APPROVAL_ONLY"
```

PowerShell:

```powershell
$env:SDRA_SAP_ASHOST = "your.sap.host"
$env:SDRA_SAP_SYSNR = "00"
$env:SDRA_SAP_CLIENT = "100"
$env:SDRA_SAP_USERNAME = "your_user"
$env:SDRA_SAP_PASSWORD = "your_password"
$env:SDRA_SAP_LANG = "EN"
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

## Test RFC Client

Edit `test_rfc.py` with a real sales order, then run:

```bash
python ./mcp_server/test_rfc.py
```

Expected result:

```text
EV_STATUS = SUCCESS
EV_APPROVAL_ID = generated approval ID
```

## MCP Tools

| Tool | Description |
|---|---|
| `sdra_check_sap_config` | Checks required SAP RFC environment variables |
| `sdra_create_approval_request` | Calls `Z_SDRA_CREATE_APPR_REQ` |
| `sdra_write_action_log` | Calls `Z_SDRA_WRITE_ACT_LOG` |
| `sdra_create_outbound_delivery` | Calls `Z_SDRA_CREATE_DELIVERY` |

## Safety

Keep:

```bash
export SDRA_ACTION_MODE="APPROVAL_ONLY"
```

In this mode, delivery creation is blocked by the MCP layer before SAP is called.


