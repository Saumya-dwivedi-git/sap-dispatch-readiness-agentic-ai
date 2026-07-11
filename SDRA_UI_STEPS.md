# SDRA UI Steps

## Folder To Open In VS Code

Open this folder:

`<local-project-folder>`

## UI Object Names

| Object Name | Description |
|---|---|
| `SDRA_DISPATCH_READINESS_AGENT_UI` | Local UI server |
| `SDRA_AGENT_CONTROL_UI` | Browser UI |
| `SDRA_DISPATCH_READINESS_AGENT_RUNNER` | Main agent runner |
| `SDRA_SAP_GATEWAY` | SAP API/OData connector |
| `ZCL_SDRA_READINESS_ENGINE` | Readiness and priority logic |

## Step 1: Open VS Code

Open the folder above in VS Code.

## Step 2: Set SAP Environment Variables

Use PowerShell terminal in VS Code.

```powershell
$env:SDRA_SAP_BASE_URL = "https://your-sap-host.example.com"
$env:SDRA_SAP_CLIENT = "100"
$env:SDRA_SAP_AUTH_MODE = "BASIC"
$env:SDRA_SAP_USERNAME = "your_sap_user"
$env:SDRA_SAP_PASSWORD = "your_sap_password"
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

For bearer token:

```powershell
$env:SDRA_SAP_BASE_URL = "https://your-sap-host.example.com"
$env:SDRA_SAP_CLIENT = "100"
$env:SDRA_SAP_AUTH_MODE = "BEARER"
$env:SDRA_SAP_BEARER_TOKEN = "your_token"
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

## Step 3: Validate SAP Config

PowerShell:

```powershell
python .\src\sdra_run_sap_agent.py --check-config
```

Git Bash:

```bash
python ./src/sdra_run_sap_agent.py --check-config
```

Expected success:

```text
SDRA_DISPATCH_READINESS_AGENT config check passed.
```

## Step 4: Start The UI

PowerShell:

```powershell
python .\src\sdra_ui_server.py
```

Git Bash:

```bash
python ./src/sdra_ui_server.py
```

Expected:

```text
SDRA_DISPATCH_READINESS_AGENT_UI running at http://127.0.0.1:8010
```

## Step 5: Open The UI

Open:

`http://127.0.0.1:8010`

## Step 6: Run From UI

In the UI:

1. Confirm `Action Mode` is `APPROVAL_ONLY`.
2. Enter the SAP connection values if they are not already set as environment variables.
3. Select the planning date.
4. Click `Check Config`.
5. Click `Run Agent`.

## Step 7: Review Results

The UI shows:

- SAP connection status
- readiness decisions from `ZCL_SDRA_READINESS_ENGINE`
- action results from `Z_SDRA_CREATE_APPR_REQ`, `Z_SDRA_CREATE_DELIVERY`, and `Z_SDRA_WRITE_ACT_LOG`
- SAP object mapping for the SDRA services

## Important Pilot Control

Keep:

```powershell
$env:SDRA_ACTION_MODE = "APPROVAL_ONLY"
```

In this mode, `SDRA_ACTION_CREATE_OUTBOUND_DELIVERY` is blocked. The agent creates approval requests first.

