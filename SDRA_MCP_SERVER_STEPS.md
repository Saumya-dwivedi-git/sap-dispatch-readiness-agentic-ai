# SDRA MCP Server Steps

## Purpose

Use an MCP server when you want the agent to call SAP through named tools instead of direct REST calls from the UI runner.

This matches the agentic pattern:

`Agent -> MCP Tool -> SAP OData/BAPI Wrapper -> SAP Result -> Agent Decision`

## MCP Server Name

`sdra-sap-mcp-server`

## Tool Names

Use these exact tool names:

| MCP Tool | SAP Endpoint / Wrapper | Description |
|---|---|---|
| `sdra_check_sap_config` | local config/env check | Checks SAP connection variables |
| `sdra_get_open_sales_orders` | `ZSDRA_DISPATCH_SRV/OpenSalesOrders` | Reads open sales orders |
| `sdra_get_stock_atp` | `ZSDRA_DISPATCH_SRV/StockAtp` | Reads ATP/stock |
| `sdra_get_delivery_status` | `ZSDRA_DISPATCH_SRV/DeliveryStatus` | Reads existing delivery status |
| `sdra_create_approval_request` | `ZSDRA_ACTION_SRV/ApprovalRequests` | Creates approval request |
| `sdra_create_outbound_delivery` | `ZSDRA_ACTION_SRV/CreateOutboundDelivery` | Creates outbound delivery after approval |
| `sdra_write_action_log` | `ZSDRA_ACTION_SRV/ActionLog` | Writes action log |

## Recommended MCP Tool Contracts

### Tool `sdra_get_open_sales_orders`

Input:

```json
{
  "planning_date": "2026-07-07",
  "horizon_days": 0,
  "plant": "1000",
  "shipping_point": "SP01"
}
```

Output:

```json
{
  "orders": [
    {
      "SalesOrder": "50001234",
      "SalesOrderItem": "000010",
      "CustomerName": "Metro Retail",
      "Material": "MAT-100",
      "Plant": "1000",
      "ShippingPoint": "SP01",
      "RequestedDeliveryDate": "2026-07-07",
      "ConfirmedQuantity": 20,
      "AvailableStockQuantity": 25,
      "CreditBlock": false,
      "DeliveryBlock": false,
      "BillingBlock": false,
      "ExistingDelivery": false
    }
  ]
}
```

### Tool `sdra_create_approval_request`

Input:

```json
{
  "approval_type": "SDRA_APPR_CREATE_FULL_DELIVERY",
  "sales_order": "50001234",
  "sales_order_item": "000010",
  "dispatch_qty": 20,
  "readiness_status": "READY_FOR_DELIVERY",
  "reason_code": "SDRA_REASON_READY_CLEAN",
  "owner_team": "Dispatch planner"
}
```

Output:

```json
{
  "approval_id": "SDRA_APPR_20260707_000001",
  "status": "CREATED",
  "message": "Approval request created"
}
```

### Tool `sdra_create_outbound_delivery`

Input:

```json
{
  "approval_id": "SDRA_APPR_20260707_000001",
  "sales_order": "50001234",
  "sales_order_item": "000010",
  "delivery_qty": 20
}
```

Output:

```json
{
  "delivery": "80001234",
  "status": "CREATED",
  "message": "Outbound delivery created"
}
```

## MCP Server Implementation Direction

You can implement the MCP server in either Python or Node.js.

Recommended for this project:

- keep current SDRA UI/agent in Python
- add MCP server as a separate folder named `mcp_server`
- expose tools above
- reuse SAP env vars:
  - `SDRA_SAP_BASE_URL`
  - `SDRA_SAP_CLIENT`
  - `SDRA_SAP_AUTH_MODE`
  - `SDRA_SAP_USERNAME`
  - `SDRA_SAP_PASSWORD`
  - `SDRA_SAP_BEARER_TOKEN`
  - `SDRA_ACTION_MODE`

## Step 1: Create MCP Server Folder

Inside this VS Code project:

```text
mcp_server/
```

Suggested files:

| File | Description |
|---|---|
| `sdra_mcp_server.py` | MCP server entrypoint |
| `sdra_mcp_sap_client.py` | SAP OData client |
| `sdra_mcp_tools.py` | Tool definitions |
| `README.md` | MCP server run steps |

## Step 2: Map MCP Tools To SAP Endpoints

Use these paths from `config/sdra_agent_config.example.json`:

```text
/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/OpenSalesOrders
/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/StockAtp
/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/DeliveryStatus
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/ApprovalRequests
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/CreateOutboundDelivery
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/ActionLog
```

## Step 3: Register MCP Server With Your Agent Client

Use the MCP server command from the project folder.

Git Bash shape:

```bash
python ./mcp_server/sdra_mcp_server.py
```

PowerShell shape:

```powershell
python .\mcp_server\sdra_mcp_server.py
```

## Step 4: Keep The Action Guardrail

MCP tool `sdra_create_outbound_delivery` must check:

```text
SDRA_ACTION_MODE = CONTROLLED_AUTONOMY
```

If the mode is `APPROVAL_ONLY`, the tool must return:

```json
{
  "status": "SKIPPED_APPROVAL_REQUIRED",
  "message": "Outbound delivery creation is blocked in approval-only mode"
}
```

## Step 5: Agent Prompt Tool Rules

The agent should follow these rules:

1. Always call `sdra_get_open_sales_orders` first.
2. Classify readiness.
3. For `READY_FOR_DELIVERY`, call `sdra_create_approval_request`.
4. For `PARTIALLY_READY`, call `sdra_create_approval_request` with partial quantity.
5. For `BLOCKED`, call `sdra_write_action_log` and escalate.
6. Never call `sdra_create_outbound_delivery` unless approval exists and action mode is `CONTROLLED_AUTONOMY`.

## Step 6: ABAP Objects Still Required

Even with MCP, SAP still needs:

- `ZSDRA_DISPATCH_SRV`
- `ZSDRA_ACTION_SRV`
- `ZSDRA_APPR_REQ`
- `ZSDRA_ACT_LOG`
- `Z_SDRA_CREATE_APPR_REQ`
- `Z_SDRA_CREATE_DELIVERY`
- `Z_SDRA_WRITE_ACT_LOG`

The MCP server is the tool layer. The ABAP services are the SAP execution layer.


