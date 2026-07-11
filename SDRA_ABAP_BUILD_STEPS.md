# SDRA ABAP Build Steps

## Agent Name

`SDRA_DISPATCH_READINESS_AGENT`

## ABAP Namespace

Use only these prefixes for this agent:

| Prefix        | Usage                                  |
| ------------- | -------------------------------------- |
| `ZSDRA_`    | DDIC tables, structures, service names |
| `ZC_SDRA_`  | CDS consumption views                  |
| `ZI_SDRA_`  | CDS interface views                    |
| `ZCL_SDRA_` | ABAP classes                           |
| `ZIF_SDRA_` | ABAP interfaces                        |
| `Z_SDRA_`   | Function modules or action wrappers    |

## Target SAP Flow

1. Agent calls MCP tool `sdra_get_open_sales_orders`.
2. MCP server calls SAP OData service `ZSDRA_DISPATCH_SRV`.
3. SAP returns open sales orders with stock, blocks, shipping point, and delivery status.
4. Agent classifies readiness.
5. Agent calls MCP tool `sdra_create_approval_request` for ready or partial orders.
6. MCP server posts approval request to SAP service `ZSDRA_ACTION_SRV`.
7. SAP writes approval/action log in `ZSDRA_APPR_REQ` and `ZSDRA_ACT_LOG`.
8. Direct delivery creation remains disabled until controlled autonomy is approved.

## Step 1: Create DDIC Tables

### Table `ZSDRA_CFG`

Purpose: agent configuration by plant and shipping point.

Suggested fields:

| Field                    | Type        | Key | Description                        |
| ------------------------ | ----------- | --: | ---------------------------------- |
| `MANDT`                | `MANDT`   | Yes | Client                             |
| `PLANT`                | `WERKS_D` | Yes | Plant                              |
| `SHIPPING_POINT`       | `VSTEL`   | Yes | Shipping point                     |
| `AUTO_CREATE_DELIVERY` | `CHAR1`   |  No | `X` only after autonomy approval |
| `CUTOFF_TIME`          | `TIMS`    |  No | Daily dispatch cut-off             |
| `ACTIVE`               | `CHAR1`   |  No | Agent active flag                  |

### Table `ZSDRA_RUN_HDR`

Purpose: one record per agent run.

Suggested fields:

| Field             | Type           | Key | Description            |
| ----------------- | -------------- | --: | ---------------------- |
| `MANDT`         | `MANDT`      | Yes | Client                 |
| `RUN_ID`        | `CHAR32`     | Yes | Agent run ID           |
| `PLANNING_DATE` | `DATS`       |  No | Dispatch planning date |
| `START_TS`      | `TIMESTAMPL` |  No | Start timestamp        |
| `END_TS`        | `TIMESTAMPL` |  No | End timestamp          |
| `STATUS`        | `CHAR20`     |  No | Run status             |

### Table `ZSDRA_RUN_ITEM`

Purpose: readiness result per sales order item.

Suggested fields:

| Field                  | Type         | Key | Description                      |
| ---------------------- | ------------ | --: | -------------------------------- |
| `MANDT`              | `MANDT`    | Yes | Client                           |
| `RUN_ID`             | `CHAR32`   | Yes | Agent run ID                     |
| `VBELN`              | `VBELN_VA` | Yes | Sales order                      |
| `POSNR`              | `POSNR_VA` | Yes | Sales order item                 |
| `READINESS_STATUS`   | `CHAR30`   |  No | Ready, blocked, partial, at risk |
| `REASON_CODE`        | `CHAR40`   |  No | SDRA reason code                 |
| `RECOMMENDED_ACTION` | `CHAR50`   |  No | SDRA action                      |
| `DISPATCH_QTY`       | `MENGE_D`  |  No | Recommended dispatch quantity    |
| `PRIORITY_SCORE`     | `INT4`     |  No | Priority score                   |

### Table `ZSDRA_APPR_REQ`

Purpose: approval queue for SAP write actions.

Suggested fields:

| Field             | Type           | Key | Description                           |
| ----------------- | -------------- | --: | ------------------------------------- |
| `MANDT`         | `MANDT`      | Yes | Client                                |
| `APPROVAL_ID`   | `CHAR32`     | Yes | Approval request ID                   |
| `RUN_ID`        | `CHAR32`     |  No | Agent run ID                          |
| `VBELN`         | `VBELN_VA`   |  No | Sales order                           |
| `POSNR`         | `POSNR_VA`   |  No | Item                                  |
| `APPROVAL_TYPE` | `CHAR40`     |  No | Full or partial delivery approval     |
| `REQUESTED_QTY` | `MENGE_D`    |  No | Requested delivery quantity           |
| `STATUS`        | `CHAR20`     |  No | Pending, approved, rejected, executed |
| `REQUESTED_BY`  | `SYUNAME`    |  No | Agent technical user                  |
| `REQUESTED_TS`  | `TIMESTAMPL` |  No | Timestamp                             |
| `APPROVED_BY`   | `SYUNAME`    |  No | Approver                              |
| `APPROVED_TS`   | `TIMESTAMPL` |  No | Approval timestamp                    |

### Table `ZSDRA_ACT_LOG`

Purpose: immutable audit log.

Suggested fields:

| Field           | Type           | Key | Description              |
| --------------- | -------------- | --: | ------------------------ |
| `MANDT`       | `MANDT`      | Yes | Client                   |
| `LOG_ID`      | `CHAR32`     | Yes | Log ID                   |
| `RUN_ID`      | `CHAR32`     |  No | Agent run ID             |
| `EVENT_NAME`  | `CHAR50`     |  No | SDRA event               |
| `ACTION_NAME` | `CHAR50`     |  No | SDRA action              |
| `VBELN`       | `VBELN_VA`   |  No | Sales order              |
| `POSNR`       | `POSNR_VA`   |  No | Item                     |
| `STATUS`      | `CHAR20`     |  No | Success, failed, skipped |
| `MESSAGE`     | `STRING`     |  No | Explanation              |
| `CREATED_BY`  | `SYUNAME`    |  No | User                     |
| `CREATED_TS`  | `TIMESTAMPL` |  No | Timestamp                |

## Step 2: Create CDS Views For Read APIs

### CDS `ZI_SDRA_SO_OPEN`

Purpose: interface view for open sales order items.

Source direction:

- `VBAK`
- `VBAP`
- `VBEP`
- `VBUP`
- `VBUK`
- `KNA1`
- `MARA`
- `MAKT`

Required output fields:

| Field Alias               | SAP Source Direction                        |
| ------------------------- | ------------------------------------------- |
| `SalesOrder`            | `VBAK-VBELN`                              |
| `SalesOrderItem`        | `VBAP-POSNR`                              |
| `SoldToParty`           | `VBAK-KUNNR`                              |
| `CustomerName`          | `KNA1-NAME1`                              |
| `Material`              | `VBAP-MATNR`                              |
| `MaterialDescription`   | `MAKT-MAKTX`                              |
| `Plant`                 | `VBAP-WERKS`                              |
| `StorageLocation`       | `VBAP-LGORT`                              |
| `ShippingPoint`         | `VBAP-VSTEL` or determined shipping point |
| `RequestedDeliveryDate` | `VBEP-EDATU`                              |
| `OrderQuantity`         | `VBAP-KWMENG`                             |
| `ConfirmedQuantity`     | confirmed schedule-line quantity            |
| `CreditBlock`           | credit status/block logic                   |
| `DeliveryBlock`         | `VBAK-LIFSK` or item block                |
| `BillingBlock`          | `VBAK-FAKSK` or item block                |

### CDS `ZC_SDRA_SO_OPEN`

Purpose: consumption view exposed to OData as `OpenSalesOrders`.

Filter parameters:

- `planning_date`
- `horizon_days`
- optional `plant`
- optional `shipping_point`

### CDS `ZC_SDRA_STOCK_ATP`

Purpose: stock/ATP by material, plant, and storage location.

Source direction:

- standard stock CDS if available
- or `MARD`, `MCHB`, ATP/check availability logic depending on your system

### CDS `ZC_SDRA_DELIVERY_STAT`

Purpose: existing delivery and PGI status.

Source direction:

- `LIPS`
- `LIKP`
- `VBFA`
- `VBUK`
- `VBUP`

## Step 3: Create OData Read Service `ZSDRA_DISPATCH_SRV`

Use SEGW or RAP/OData depending on your system standard.

Service name:

`ZSDRA_DISPATCH_SRV`

Entity sets:

| Entity Set          | Backing Object            | Description                      |
| ------------------- | ------------------------- | -------------------------------- |
| `OpenSalesOrders` | `ZC_SDRA_SO_OPEN`       | Agent open sales order input     |
| `StockAtp`        | `ZC_SDRA_STOCK_ATP`     | Agent availability check         |
| `DeliveryStatus`  | `ZC_SDRA_DELIVERY_STAT` | Existing delivery and PGI status |

Gateway path expected by the Python agent:

`/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/OpenSalesOrders`

## Step 4: Create ABAP Interface `ZIF_SDRA_SAP_GATEWAY`

Purpose: one ABAP contract for SDRA actions.

Methods:

| Method                       | Description                             |
| ---------------------------- | --------------------------------------- |
| `GET_OPEN_SALES_ORDERS`    | Read order lines for planning date      |
| `GET_STOCK_ATP`            | Read stock/ATP                          |
| `GET_DELIVERY_STATUS`      | Read delivery status                    |
| `CREATE_APPROVAL_REQUEST`  | Create action approval request          |
| `CREATE_OUTBOUND_DELIVERY` | Create outbound delivery after approval |
| `WRITE_ACTION_LOG`         | Write audit log                         |

## Step 5: Create ABAP Classes

### Class `ZCL_SDRA_READINESS_ENGINE`

Purpose: optional SAP-side mirror of readiness logic.

Keep the same statuses as the Python agent:

- `READY_FOR_DELIVERY`
- `PARTIALLY_READY`
- `BLOCKED`
- `AT_RISK`
- `ALREADY_IN_DELIVERY`
- `NOT_DUE_FOR_DISPATCH`

### Class `ZCL_SDRA_ACTION_ENGINE`

Purpose: decide SAP action based on readiness result.

Actions:

- `SDRA_ACTION_REQUEST_DELIVERY_APPROVAL`
- `SDRA_ACTION_CREATE_OUTBOUND_DELIVERY`
- `SDRA_ACTION_ESCALATE_BLOCKED_ORDER`
- `SDRA_ACTION_MONITOR_PGI_STATUS`

### Class `ZCL_SDRA_LOGGER`

Purpose: write `ZSDRA_ACT_LOG`.

Every action must log:

- input sales order
- readiness status
- reason code
- action name
- result status
- message
- timestamp

## Step 6: Create OData Action Service `ZSDRA_ACTION_SRV`

Service name:

`ZSDRA_ACTION_SRV`

Entity sets/actions:

| Endpoint                   | ABAP Object                | Description                     |
| -------------------------- | -------------------------- | ------------------------------- |
| `ApprovalRequests`       | `Z_SDRA_CREATE_APPR_REQ` | Creates approval request        |
| `CreateOutboundDelivery` | `Z_SDRA_CREATE_DELIVERY` | Creates delivery after approval |
| `ActionLog`              | `Z_SDRA_WRITE_ACT_LOG`   | Writes agent log                |

Python config expects:

```text
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/ApprovalRequests
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/CreateOutboundDelivery
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/ActionLog
```

## Step 7: Create Wrapper `Z_SDRA_CREATE_APPR_REQ`

Purpose: create row in `ZSDRA_APPR_REQ`.

Input payload:

| Field                | Description                                                                 |
| -------------------- | --------------------------------------------------------------------------- |
| `approval_type`    | `SDRA_APPR_CREATE_FULL_DELIVERY` or `SDRA_APPR_CREATE_PARTIAL_DELIVERY` |
| `sales_order`      | Sales order                                                                 |
| `sales_order_item` | Item                                                                        |
| `dispatch_qty`     | Proposed delivery quantity                                                  |
| `reason_code`      | SDRA reason                                                                 |
| `readiness_status` | SDRA readiness status                                                       |
| `owner_team`       | Responsible owner                                                           |

Return payload:

| Field            | Description       |
| ---------------- | ----------------- |
| `sap_document` | Approval ID       |
| `status`       | Success or failed |
| `message`      | Result message    |

## Step 8: Create Wrapper `Z_SDRA_CREATE_DELIVERY`

Purpose: controlled outbound delivery creation.

Recommended internal call options:

- `BAPI_OUTB_DELIVERY_CREATE_SLS`
- or your existing delivery creation wrapper
- or standard API in S/4HANA if available in your landscape

Mandatory checks before creation:

1. Approval exists in `ZSDRA_APPR_REQ`.
2. Approval status is `APPROVED`.
3. No credit block.
4. No delivery block.
5. No billing block.
6. No existing delivery for the same item.
7. Dispatch quantity is not greater than confirmed quantity.
8. Plant and shipping point are active in `ZSDRA_CFG`.

Never allow the wrapper to bypass block statuses.

## Step 9: Create Wrapper `Z_SDRA_WRITE_ACT_LOG`

Purpose: write every agent decision and SAP action result to `ZSDRA_ACT_LOG`.

Keep this endpoint active even when delivery creation is disabled. It is needed for auditability.

## Step 10: Activate Gateway Services

In SAP Gateway:

1. Go to `/IWFND/MAINT_SERVICE`.
2. Add service `ZSDRA_DISPATCH_SRV`.
3. Add service `ZSDRA_ACTION_SRV`.
4. Activate SICF nodes if required.
5. Test metadata:

```text
/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/$metadata
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/$metadata
```

## Step 11: Create Technical User And Authorizations

Technical user:

`SDRA_AGENT_USER`

Minimum authorization direction:

- read sales orders
- read stock
- read delivery status
- create records in `ZSDRA_APPR_REQ`
- write records in `ZSDRA_ACT_LOG`
- execute `Z_SDRA_CREATE_DELIVERY` only after approval

Do not give broad SAP_ALL access.

## Step 12: Test OData With Browser Or Postman

Read test:

```text
https://your-sap-host.example.com/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/OpenSalesOrders?planning_date=2026-07-07&horizon_days=0&sap-client=100
```

Expected JSON should include:

- `SalesOrder`
- `SalesOrderItem`
- `CustomerName`
- `Material`
- `Plant`
- `ShippingPoint`
- `RequestedDeliveryDate`
- `ConfirmedQuantity`
- `AvailableStockQuantity`
- `CreditBlock`
- `DeliveryBlock`
- `BillingBlock`
- `ExistingDelivery`

## Step 13: Connect Python Agent

In Git Bash:

```bash
cd <local-project-folder>
export SDRA_SAP_BASE_URL="https://your-sap-host.example.com"
export SDRA_SAP_CLIENT="100"
export SDRA_SAP_AUTH_MODE="BASIC"
export SDRA_SAP_USERNAME="SDRA_AGENT_USER"
export SDRA_SAP_PASSWORD="your_password"
export SDRA_ACTION_MODE="APPROVAL_ONLY"
python ./src/sdra_run_sap_agent.py --check-config
```

Start UI:

```bash
python ./src/sdra_ui_server.py
```

Open:

```text
http://127.0.0.1:8010
```

