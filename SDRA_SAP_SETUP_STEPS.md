# SDRA SAP Setup Steps

## Main Agent Runner

Run object:

`SDRA_DISPATCH_READINESS_AGENT`

Main file:

`src/sdra_run_sap_agent.py`

## Required SAP Environment Variables

Set these in PowerShell before running the SAP-connected agent.

```powershell
$env:SDRA_SAP_BASE_URL = "https://your-sap-host.example.com"
$env:SDRA_SAP_CLIENT = "100"
$env:SDRA_SAP_AUTH_MODE = "BASIC"
$env:SDRA_SAP_USERNAME = "your_sap_user"
$env:SDRA_SAP_PASSWORD = "your_sap_password"
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

For bearer-token authentication:

```powershell
$env:SDRA_SAP_BASE_URL = "https://your-sap-host.example.com"
$env:SDRA_SAP_CLIENT = "100"
$env:SDRA_SAP_AUTH_MODE = "BEARER"
$env:SDRA_SAP_BEARER_TOKEN = "your_token"
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

## Validate Configuration

```powershell
python .\outputs\sdra_sap_dispatch_readiness_agent\src\sdra_run_sap_agent.py --check-config
```

## Run Agent Against SAP

```powershell
python .\outputs\sdra_sap_dispatch_readiness_agent\src\sdra_run_sap_agent.py --planning-date 2026-07-07
```

## SAP Services To Provide

Update:

`config/sdra_agent_config.example.json`

with the final SAP service paths.

| Config Key | SAP Object Name | Description |
|---|---|---|
| `open_sales_orders_path` | `ZC_SDRA_SO_OPEN` | Open sales orders for dispatch readiness |
| `stock_atp_path` | `ZC_SDRA_STOCK_ATP` | Available stock and ATP |
| `delivery_status_path` | `ZC_SDRA_DELIVERY_STAT` | Existing delivery and PGI status |
| `approval_request_path` | `Z_SDRA_CREATE_APPR_REQ` | Approval request creation |
| `create_delivery_path` | `Z_SDRA_CREATE_DELIVERY` | Controlled outbound delivery creation |
| `action_log_path` | `Z_SDRA_WRITE_ACT_LOG` | Agent action log write-back |

## MVP Action Mode

Keep this for pilot:

```powershell
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

In this mode, the agent will not directly create outbound deliveries. It will create approval requests for:

- `SDRA_APPR_CREATE_FULL_DELIVERY`
- `SDRA_APPR_CREATE_PARTIAL_DELIVERY`

Only switch to controlled autonomy after validation:

```powershell
$env:SDRA_ACTION_MODE = "CONTROLLED_AUTONOMY"
```


