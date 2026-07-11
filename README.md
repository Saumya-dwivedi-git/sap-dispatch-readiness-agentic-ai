# SDRA Dispatch Readiness SAP Agent

## Agent Object

`SDRA_DISPATCH_READINESS_AGENT`

## Description

SAP-connected agentic AI for sales order dispatch readiness. The agent reads open sales orders from SAP, checks delivery readiness, decides the next best action, creates approval requests for delivery creation, escalates blocked orders, and writes an action log.

This folder is intentionally separate from other agents and contains only the SAP-connected build path.

## Portfolio / GitHub Showcase Note

This repository is a sanitized showcase copy. It uses placeholder SAP connection values and excludes runtime logs, credentials, and private system details. For a demo, use screenshots, sample payloads, or a local SAP-connected run from an approved environment.

Start with:

- `GITHUB_UPLOAD_STEPS.md` for upload instructions
- `SECURITY_AND_DEMO_NOTES.md` for what is safe to share
- `docs/ARCHITECTURE.md` for the system architecture diagram
- `docs/AGENT_FLOW.md` for the agentic execution flow
- `sample_data/open_sales_orders_sample.json` for a non-confidential example payload

## Main Files

| File | Object Name | Description |
|---|---|---|
| `src/sdra_run_sap_agent.py` | `SDRA_DISPATCH_READINESS_AGENT_RUNNER` | Main runner for the SAP-connected agent |
| `src/sdra_agentic_core.py` | `SDRA_DISPATCH_READINESS_AGENT` | Observe, analyze, decide, act, and monitor loop |
| `src/sdra_sap_gateway.py` | `SDRA_SAP_GATEWAY` | SAP API/OData gateway and controlled write-action wrapper |
| `src/sdra_readiness_engine.py` | `ZCL_SDRA_READINESS_ENGINE` | Readiness classification and priority logic |
| `src/sdra_models.py` | `SDRA_DOMAIN_MODELS` | Agent data objects |
| `src/sdra_ui_server.py` | `SDRA_DISPATCH_READINESS_AGENT_UI` | Local web UI server for SAP-connected agent control |
| `ui/index.html` | `SDRA_AGENT_CONTROL_UI` | Browser interface for config, run control, readiness decisions, and action results |
| `config/sdra_agent_config.example.json` | `SDRA_AGENT_CONFIG_TEMPLATE` | SAP endpoint and action-mode config |
| `SDRA_SAP_CONNECTION_SPEC.md` | `SDRA_SAP_CONNECTION_SPEC` | SAP service and wrapper design |
| `SDRA_SAP_SETUP_STEPS.md` | `SDRA_SAP_SETUP_STEPS` | Environment variables and run commands |
| `SDRA_ABAP_BUILD_STEPS.md` | `SDRA_ABAP_BUILD_STEPS` | ABAP developer build guide for DDIC, CDS, OData, wrappers, and authorizations |
| `SDRA_ECLIPSE_ADT_STEPS_AND_CODE.md` | `SDRA_ECLIPSE_ADT_STEPS_AND_CODE` | Eclipse ADT steps with ABAP/CDS starter code |
| `SDRA_MCP_SERVER_STEPS.md` | `SDRA_MCP_SERVER_STEPS` | MCP server tool design and SAP endpoint mapping |
| `mcp_server/` | `sdra-sap-mcp-server` | MCP/RFC tool layer for calling SDRA SAP function modules |

## SAP Objects

| SAP Object | Description |
|---|---|
| `ZC_SDRA_SO_OPEN` | Open sales order lines for dispatch readiness |
| `ZC_SDRA_STOCK_ATP` | Stock and ATP data |
| `ZC_SDRA_DELIVERY_STAT` | Existing delivery and PGI status |
| `Z_SDRA_CREATE_APPR_REQ` | Approval request creation wrapper |
| `Z_SDRA_CREATE_DELIVERY` | Controlled outbound delivery creation wrapper |
| `Z_SDRA_WRITE_ACT_LOG` | Agent action log write-back wrapper |

## ABAP Developer Start Here

1. Build SAP-side objects from `SDRA_ABAP_BUILD_STEPS.md`.
2. Use `SDRA_ECLIPSE_ADT_STEPS_AND_CODE.md` for Eclipse ADT object creation and starter code.
3. Expose services `ZSDRA_DISPATCH_SRV` and `ZSDRA_ACTION_SRV`.
4. Test the OData endpoints in `/IWFND/GW_CLIENT`, browser, or Postman.
5. Add MCP server tools from `SDRA_MCP_SERVER_STEPS.md` if you want the same MCP pattern as the previous agent.
6. Run the UI after SAP endpoints and credentials are ready.

## MCP Server Folder

The MCP/RFC starter files are in:

```text
mcp_server
```

Start with:

```text
mcp_server/README.md
```

## VS Code Tasks

Use **Terminal > Run Task**:

- `SDRA: Check SAP Config`
- `SDRA: Run SAP Agent`
- `SDRA: Start UI`

## UI URL

After starting the UI server:

`http://127.0.0.1:8010`

## First Required Setup

Set SAP variables in PowerShell or copy `.env.example` into your enterprise-approved secret flow.

```powershell
$env:SDRA_SAP_BASE_URL = "https://your-sap-host.example.com"
$env:SDRA_SAP_CLIENT = "100"
$env:SDRA_SAP_AUTH_MODE = "BASIC"
$env:SDRA_SAP_USERNAME = "your_sap_user"
$env:SDRA_SAP_PASSWORD = "your_sap_password"
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

Then validate:

```powershell
python .\src\sdra_run_sap_agent.py --check-config
```

If your VS Code terminal is Git Bash, use:

```bash
python ./src/sdra_run_sap_agent.py --check-config
```

Start the UI in Git Bash:

```bash
python ./src/sdra_ui_server.py
```

