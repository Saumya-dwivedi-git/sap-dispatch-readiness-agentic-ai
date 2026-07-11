# SDRA Agent Objects

## Primary Agent

| Object Name | Description |
|---|---|
| `SDRA_DISPATCH_READINESS_AGENT` | Main SAP-connected action agent for sales order dispatch readiness |

## Runtime Objects

| Object Name | File | Description |
|---|---|---|
| `SDRA_DISPATCH_READINESS_AGENT_RUNNER` | `src/sdra_run_sap_agent.py` | Loads config, validates SAP connection, and starts the agent |
| `SDRA_AGENTIC_CORE` | `src/sdra_agentic_core.py` | Executes observe, analyze, decide, act, and monitor |
| `SDRA_SAP_GATEWAY` | `src/sdra_sap_gateway.py` | Connects to SAP OData/API endpoints and controlled write wrappers |
| `ZCL_SDRA_READINESS_ENGINE` | `src/sdra_readiness_engine.py` | Applies readiness and priority rules |
| `SDRA_DOMAIN_MODELS` | `src/sdra_models.py` | Defines sales order, decision, and action result objects |

## SAP Action Objects

| Object Name | Description |
|---|---|
| `SDRA_ACTION_SCAN_OPEN_SALES_ORDERS` | Reads open SAP sales order lines |
| `SDRA_ACTION_CHECK_DELIVERY_READINESS` | Determines readiness status |
| `SDRA_ACTION_REQUEST_DELIVERY_APPROVAL` | Creates approval request for full or partial delivery |
| `SDRA_ACTION_CREATE_OUTBOUND_DELIVERY` | Creates outbound delivery after approval or controlled autonomy |
| `SDRA_ACTION_ESCALATE_BLOCKED_ORDER` | Escalates credit, delivery, billing, stock, or master data blocks |
| `SDRA_ACTION_MONITOR_PGI_STATUS` | Monitors delivery execution and goods issue status |


