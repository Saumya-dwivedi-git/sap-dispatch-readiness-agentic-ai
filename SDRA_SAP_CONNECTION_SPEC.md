# SDRA SAP Connection Specification

## Purpose

This file defines the SAP-connected build path for `SDRA_DISPATCH_READINESS_AGENT`.

The agent is not an Excel bot. It is designed to connect to SAP through approved APIs, CDS/OData services, or controlled BAPI/RFC wrappers.

## Connection Object Names

| Object Name | Type | Description |
|---|---|---|
| `SDRA_SAP_CONNECTION` | Runtime connection | Holds SAP base URL, client, auth mode, timeout, and action mode |
| `SDRA_SAP_GATEWAY` | Python object | Executes SAP read calls and controlled write calls |
| `ZIF_SDRA_SAP_GATEWAY` | SAP interface | ABAP-side contract for SDRA read and write operations |
| `Z_SDRA_CREATE_DELIVERY` | SAP wrapper | Creates outbound delivery only after approval or allowed autonomy |
| `Z_SDRA_CREATE_APPR_REQ` | SAP wrapper | Creates approval request for delivery or partial delivery |
| `Z_SDRA_WRITE_ACT_LOG` | SAP wrapper | Writes action log to SAP |

## Required SAP Read Services

| SDRA Service Name | Recommended SAP Object | Description |
|---|---|---|
| `SDRA_SRV_OPEN_SALES_ORDERS` | `ZC_SDRA_SO_OPEN` or standard Sales Order API | Returns open sales order lines due today, overdue, or in planning horizon |
| `SDRA_SRV_STOCK_ATP` | `ZC_SDRA_STOCK_ATP` or ATP/stock API | Returns available stock by material, plant, and storage location |
| `SDRA_SRV_DELIVERY_STATUS` | `ZC_SDRA_DELIVERY_STAT` or delivery API | Returns existing outbound delivery and PGI status |
| `SDRA_SRV_BLOCK_STATUS` | Sales order status API/CDS | Returns credit, delivery, billing, and incompletion blocks |

## Required SAP Write Services

| SDRA Action | SAP Wrapper | MVP Mode |
|---|---|---|
| `SDRA_ACTION_REQUEST_DELIVERY_APPROVAL` | `Z_SDRA_CREATE_APPR_REQ` | Enabled |
| `SDRA_ACTION_CREATE_OUTBOUND_DELIVERY` | `Z_SDRA_CREATE_DELIVERY` | Approval required |
| `SDRA_ACTION_ESCALATE_BLOCKED_ORDER` | `Z_SDRA_SEND_NOTIFICATION` | Enabled |
| `SDRA_ACTION_WRITE_AGENT_LOG` | `Z_SDRA_WRITE_ACT_LOG` | Enabled if available |

## Authentication

Use environment variables or the enterprise secret manager. Do not store credentials in code.

| Environment Variable | Description |
|---|---|
| `SDRA_SAP_BASE_URL` | SAP Gateway or BTP destination base URL |
| `SDRA_SAP_CLIENT` | SAP client, for example `100` |
| `SDRA_SAP_AUTH_MODE` | `BASIC`, `BEARER`, or `DESTINATION` |
| `SDRA_SAP_USERNAME` | Username for basic auth, if used |
| `SDRA_SAP_PASSWORD` | Password for basic auth, if used |
| `SDRA_SAP_BEARER_TOKEN` | Bearer token, if used |
| `SDRA_ACTION_MODE` | `APPROVAL_ONLY` or `CONTROLLED_AUTONOMY` |

## Endpoint Placeholders

Update `config/sdra_agent_config.example.json` with the actual SAP endpoints.

| Config Key | Example Placeholder |
|---|---|
| `open_sales_orders_path` | `/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/OpenSalesOrders` |
| `stock_atp_path` | `/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/StockAtp` |
| `delivery_status_path` | `/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/DeliveryStatus` |
| `approval_request_path` | `/sap/opu/odata/sap/ZSDRA_ACTION_SRV/ApprovalRequests` |
| `create_delivery_path` | `/sap/opu/odata/sap/ZSDRA_ACTION_SRV/CreateOutboundDelivery` |
| `action_log_path` | `/sap/opu/odata/sap/ZSDRA_ACTION_SRV/ActionLog` |

## Write-Action Guardrail

In MVP, `SDRA_ACTION_CREATE_OUTBOUND_DELIVERY` does not post directly. The agent calls `SDRA_ACTION_REQUEST_DELIVERY_APPROVAL` and logs the proposed delivery action.

Direct delivery creation is allowed only when:

- `SDRA_ACTION_MODE = CONTROLLED_AUTONOMY`
- order status is `READY_FOR_DELIVERY`
- no credit block exists
- no delivery block exists
- no billing block exists
- no existing delivery exists
- full confirmed quantity is available
- plant and shipping point are configured as autonomous in SAP config


