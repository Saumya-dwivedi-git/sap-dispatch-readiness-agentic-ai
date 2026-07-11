# SDRA Eclipse ADT Steps And Code

## Purpose

Build SAP backend objects for:

`SDRA_DISPATCH_READINESS_AGENT`

Use Eclipse ADT for DDIC/CDS/classes, then activate Gateway/OData in SAP GUI where required.

## Step 1: Create ABAP Package

In Eclipse ADT:

1. Open ABAP perspective.
2. Right-click your system.
3. Choose **New > ABAP Package**.
4. Create package:

```text
ZSDRA_DISPATCH_AGENT
```

Description:

```text
SDRA Dispatch Readiness Agent
```

## Step 2: Create DDIC Tables

Create these transparent tables in ADT or SE11:

```text
ZSDRA_CFG
ZSDRA_RUN_HDR
ZSDRA_RUN_ITEM
ZSDRA_APPR_REQ
ZSDRA_ACT_LOG
```

If your system supports ADT table creation, use **New > Other ABAP Repository Object > Dictionary > Database Table**.

### Table `ZSDRA_CFG`

Fields:

```text
MANDT             MANDT      Key
PLANT             WERKS_D    Key
SHIPPING_POINT    VSTEL      Key
AUTO_CREATE_DEL   CHAR1
CUTOFF_TIME       TIMS
ACTIVE            CHAR1
CREATED_BY        SYUNAME
CREATED_ON        DATS
CHANGED_BY        SYUNAME
CHANGED_ON        DATS
```

### Table `ZSDRA_APPR_REQ`

Fields:

```text
MANDT             MANDT       Key
APPROVAL_ID       CHAR32      Key
RUN_ID            CHAR32
VBELN             VBELN_VA
POSNR             POSNR_VA
APPROVAL_TYPE     CHAR40
REQUESTED_QTY     MENGE_D
READINESS_STATUS  CHAR30
REASON_CODE       CHAR40
OWNER_TEAM        CHAR40
STATUS            CHAR20
REQUESTED_BY      SYUNAME
REQUESTED_TS      TIMESTAMPL
APPROVED_BY       SYUNAME
APPROVED_TS       TIMESTAMPL
```

### Table `ZSDRA_ACT_LOG`

Fields:

```text
MANDT             MANDT       Key
LOG_ID            CHAR32      Key
RUN_ID            CHAR32
EVENT_NAME        CHAR50
ACTION_NAME       CHAR50
VBELN             VBELN_VA
POSNR             POSNR_VA
STATUS            CHAR20
MESSAGE           STRING
CREATED_BY        SYUNAME
CREATED_TS        TIMESTAMPL
```

## Step 3: Create CDS View `ZI_SDRA_SO_OPEN`

In Eclipse ADT:

1. Right-click package `ZSDRA_DISPATCH_AGENT`.
2. Choose **New > Data Definition**.
3. Name:

```text
ZI_SDRA_SO_OPEN
```

Paste and adapt:

```abap
@AbapCatalog.sqlViewName: 'ZISDRASOOPEN'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'SDRA Open Sales Order Interface View'
define view ZI_SDRA_SO_OPEN
  as select from vbak
    inner join vbap on vbap.vbeln = vbak.vbeln
    left outer join kna1 on kna1.kunnr = vbak.kunnr
    left outer join makt on makt.matnr = vbap.matnr
                         and makt.spras = $session.system_language
{
  key vbak.vbeln       as SalesOrder,
  key vbap.posnr       as SalesOrderItem,
      vbak.kunnr       as SoldToParty,
      kna1.name1       as CustomerName,
      vbap.matnr       as Material,
      makt.maktx       as MaterialDescription,
      vbap.werks       as Plant,
      vbap.lgort       as StorageLocation,
      vbap.vstel       as ShippingPoint,
      vbak.vdatu       as RequestedDeliveryDate,
      vbap.kwmeng      as OrderQuantity,
      vbap.kbmeng      as ConfirmedQuantity,
      vbak.lifsk       as DeliveryBlockCode,
      vbak.faksk       as BillingBlockCode,
      case
        when vbak.lifsk <> '' then 'X'
        else ''
      end              as DeliveryBlock,
      case
        when vbak.faksk <> '' then 'X'
        else ''
      end              as BillingBlock
}
where vbak.vbtyp = 'C'
```

Notes:

- `VBAP-KBMENG` may not match your confirmed quantity logic. If your system relies on schedule lines, calculate confirmation from `VBEP`.
- Credit block logic differs by ECC/S/4 setup. Add it in a later CDS or class if needed.
- Existing delivery should normally be derived through document flow `VBFA` or delivery tables `LIKP/LIPS`.

## Step 4: Create CDS View `ZC_SDRA_SO_OPEN`

Create data definition:

```text
ZC_SDRA_SO_OPEN
```

```abap
@AbapCatalog.sqlViewName: 'ZCSDRASOOPEN'
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'SDRA Open Sales Orders Consumption View'
@OData.publish: true
define view ZC_SDRA_SO_OPEN
  as select from ZI_SDRA_SO_OPEN
{
  key SalesOrder,
  key SalesOrderItem,
      SoldToParty,
      CustomerName,
      Material,
      MaterialDescription,
      Plant,
      StorageLocation,
      ShippingPoint,
      RequestedDeliveryDate,
      OrderQuantity,
      ConfirmedQuantity,
      cast( 0 as abap.dec( 15, 3 ) ) as AvailableStockQuantity,
      cast( '' as abap.char( 1 ) )   as CreditBlock,
      DeliveryBlock,
      BillingBlock,
      cast( '' as abap.char( 1 ) )   as ExistingDelivery,
      cast( '17:00' as abap.char( 5 ) ) as DeliveryCutoffTime
}
```

After activation, SAP creates an auto OData service. For a production build, use SEGW/RAP service binding for cleaner entity names.

## Step 5: Create CDS View `ZC_SDRA_DELIVERY_STAT`

```abap
@AbapCatalog.sqlViewName: 'ZCSDRADELSTAT'
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'SDRA Delivery Status'
@OData.publish: true
define view ZC_SDRA_DELIVERY_STAT
  as select from lips
    inner join likp on likp.vbeln = lips.vbeln
{
  key lips.vgbel as SalesOrder,
  key lips.vgpos as SalesOrderItem,
  key lips.vbeln as DeliveryDocument,
      lips.posnr as DeliveryItem,
      likp.wadat_ist as ActualGoodsIssueDate,
      likp.wbstk as GoodsMovementStatus,
      likp.pkstk as PackingStatus,
      likp.kostk as PickingStatus
}
where lips.vgbel <> ''
```

## Step 6: Create Class `ZCL_SDRA_LOGGER`

Create ABAP class:

```text
ZCL_SDRA_LOGGER
```

Definition:

```abap
CLASS zcl_sdra_logger DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    CLASS-METHODS write_log
      IMPORTING
        iv_run_id      TYPE char32 OPTIONAL
        iv_event_name  TYPE char50
        iv_action_name TYPE char50 OPTIONAL
        iv_vbeln       TYPE vbeln_va OPTIONAL
        iv_posnr       TYPE posnr_va OPTIONAL
        iv_status      TYPE char20
        iv_message     TYPE string.
ENDCLASS.
```

Implementation:

```abap
CLASS zcl_sdra_logger IMPLEMENTATION.
  METHOD write_log.
    DATA lv_ts TYPE timestampl.
    GET TIME STAMP FIELD lv_ts.

    DATA ls_log TYPE zsdra_act_log.
    TRY.
        ls_log-log_id = cl_system_uuid=>create_uuid_c32_static( ).
      CATCH cx_uuid_error.
        ls_log-log_id = |LOG{ sy-datum }{ sy-uzeit }|.
    ENDTRY.

    ls_log-run_id      = iv_run_id.
    ls_log-event_name  = iv_event_name.
    ls_log-action_name = iv_action_name.
    ls_log-vbeln       = iv_vbeln.
    ls_log-posnr       = iv_posnr.
    ls_log-status      = iv_status.
    ls_log-message     = iv_message.
    ls_log-created_by  = sy-uname.
    ls_log-created_ts  = lv_ts.

    INSERT zsdra_act_log FROM ls_log.
    COMMIT WORK.
  ENDMETHOD.
ENDCLASS.
```

## Step 7: Create Class `ZCL_SDRA_ACTION_ENGINE`

```abap
CLASS zcl_sdra_action_engine DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    TYPES: BEGIN OF ty_approval_request,
             approval_type    TYPE char40,
             sales_order      TYPE vbeln_va,
             sales_order_item TYPE posnr_va,
             dispatch_qty     TYPE menge_d,
             readiness_status TYPE char30,
             reason_code      TYPE char40,
             owner_team       TYPE char40,
           END OF ty_approval_request.

    CLASS-METHODS create_approval_request
      IMPORTING is_request TYPE ty_approval_request
      RETURNING VALUE(rv_approval_id) TYPE char32.
ENDCLASS.
```

```abap
CLASS zcl_sdra_action_engine IMPLEMENTATION.
  METHOD create_approval_request.
    DATA lv_ts TYPE timestampl.
    GET TIME STAMP FIELD lv_ts.

    TRY.
        rv_approval_id = cl_system_uuid=>create_uuid_c32_static( ).
      CATCH cx_uuid_error.
        rv_approval_id = |APR{ sy-datum }{ sy-uzeit }|.
    ENDTRY.

    DATA ls_req TYPE zsdra_appr_req.
    ls_req-approval_id      = rv_approval_id.
    ls_req-vbeln            = is_request-sales_order.
    ls_req-posnr            = is_request-sales_order_item.
    ls_req-approval_type    = is_request-approval_type.
    ls_req-requested_qty    = is_request-dispatch_qty.
    ls_req-readiness_status = is_request-readiness_status.
    ls_req-reason_code      = is_request-reason_code.
    ls_req-owner_team       = is_request-owner_team.
    ls_req-status           = 'PENDING'.
    ls_req-requested_by     = sy-uname.
    ls_req-requested_ts     = lv_ts.

    INSERT zsdra_appr_req FROM ls_req.
    COMMIT WORK.

    zcl_sdra_logger=>write_log(
      iv_event_name  = 'SDRA_EVENT_APPROVAL_REQUIRED'
      iv_action_name = 'SDRA_ACTION_REQUEST_DELIVERY_APPROVAL'
      iv_vbeln       = is_request-sales_order
      iv_posnr       = is_request-sales_order_item
      iv_status      = 'SUCCESS'
      iv_message     = |Approval request { rv_approval_id } created| ).
  ENDMETHOD.
ENDCLASS.
```

## Step 8: Create Function Module `Z_SDRA_CREATE_APPR_REQ`

Create a function group, for example:

```text
ZSDRA_ACTIONS
```

Create function module:

```text
Z_SDRA_CREATE_APPR_REQ
```

Import parameters:

```text
IV_APPROVAL_TYPE     TYPE CHAR40
IV_SALES_ORDER       TYPE VBELN_VA
IV_SALES_ORDER_ITEM  TYPE POSNR_VA
IV_DISPATCH_QTY      TYPE MENGE_D
IV_READINESS_STATUS  TYPE CHAR30
IV_REASON_CODE       TYPE CHAR40
IV_OWNER_TEAM        TYPE CHAR40
```

Export parameters:

```text
EV_APPROVAL_ID       TYPE CHAR32
EV_STATUS            TYPE CHAR20
EV_MESSAGE           TYPE STRING
```

Code:

```abap
DATA ls_request TYPE zcl_sdra_action_engine=>ty_approval_request.

ls_request-approval_type    = iv_approval_type.
ls_request-sales_order      = iv_sales_order.
ls_request-sales_order_item = iv_sales_order_item.
ls_request-dispatch_qty     = iv_dispatch_qty.
ls_request-readiness_status = iv_readiness_status.
ls_request-reason_code      = iv_reason_code.
ls_request-owner_team       = iv_owner_team.

TRY.
    ev_approval_id = zcl_sdra_action_engine=>create_approval_request( ls_request ).
    ev_status = 'SUCCESS'.
    ev_message = |Approval request { ev_approval_id } created|.
  CATCH cx_root INTO DATA(lx_error).
    ev_status = 'FAILED'.
    ev_message = lx_error->get_text( ).
ENDTRY.
```

## Step 9: Create Function Module `Z_SDRA_WRITE_ACT_LOG`

Import parameters:

```text
IV_RUN_ID       TYPE CHAR32
IV_EVENT_NAME   TYPE CHAR50
IV_ACTION_NAME  TYPE CHAR50
IV_VBELN        TYPE VBELN_VA
IV_POSNR        TYPE POSNR_VA
IV_STATUS       TYPE CHAR20
IV_MESSAGE      TYPE STRING
```

Code:

```abap
TRY.
    zcl_sdra_logger=>write_log(
      iv_run_id      = iv_run_id
      iv_event_name  = iv_event_name
      iv_action_name = iv_action_name
      iv_vbeln       = iv_vbeln
      iv_posnr       = iv_posnr
      iv_status      = iv_status
      iv_message     = iv_message ).
  CATCH cx_root.
ENDTRY.
```

## Step 10: Create Function Module `Z_SDRA_CREATE_DELIVERY`

Keep this approval-controlled.

Import parameters:

```text
IV_APPROVAL_ID       TYPE CHAR32
IV_SALES_ORDER       TYPE VBELN_VA
IV_SALES_ORDER_ITEM  TYPE POSNR_VA
IV_DELIVERY_QTY      TYPE MENGE_D
```

Export parameters:

```text
EV_DELIVERY          TYPE VBELN_VL
EV_STATUS            TYPE CHAR20
EV_MESSAGE           TYPE STRING
```

Starter code:

```abap
SELECT SINGLE *
  FROM zsdra_appr_req
  WHERE approval_id = @iv_approval_id
    AND vbeln       = @iv_sales_order
    AND posnr       = @iv_sales_order_item
  INTO @DATA(ls_approval).

IF sy-subrc <> 0.
  ev_status = 'FAILED'.
  ev_message = 'Approval request not found'.
  RETURN.
ENDIF.

IF ls_approval-status <> 'APPROVED'.
  ev_status = 'SKIPPED_APPROVAL_REQUIRED'.
  ev_message = 'Approval request is not approved'.
  RETURN.
ENDIF.

" Add your block, duplicate delivery, and quantity checks here.
" Then call your company delivery wrapper or BAPI_OUTB_DELIVERY_CREATE_SLS.

ev_status = 'SKIPPED_NOT_IMPLEMENTED'.
ev_message = 'Connect company delivery creation wrapper here'.
```

## Step 11: Create OData Services

For quick CDS-published services:

1. Activate CDS with `@OData.publish: true`.
2. Go to SAP GUI transaction `/IWFND/MAINT_SERVICE`.
3. Add generated service for `ZC_SDRA_SO_OPEN`.
4. Add generated service for `ZC_SDRA_DELIVERY_STAT`.

For cleaner production design, create SEGW project:

```text
ZSDRA_DISPATCH_SRV
```

Entity sets:

```text
OpenSalesOrders
StockAtp
DeliveryStatus
```

Create second SEGW project:

```text
ZSDRA_ACTION_SRV
```

Entity sets/actions:

```text
ApprovalRequests
CreateOutboundDelivery
ActionLog
```

## Step 12: Test In SAP Gateway Client

Transaction:

```text
/IWFND/GW_CLIENT
```

Test metadata:

```text
/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/$metadata
/sap/opu/odata/sap/ZSDRA_ACTION_SRV/$metadata
```

Test read:

```text
/sap/opu/odata/sap/ZSDRA_DISPATCH_SRV/OpenSalesOrders?$top=10
```

## Step 13: Connect To Local UI

In Git Bash from this VS Code folder:

```bash
export SDRA_SAP_BASE_URL="https://your-sap-host.example.com"
export SDRA_SAP_CLIENT="100"
export SDRA_SAP_AUTH_MODE="BASIC"
export SDRA_SAP_USERNAME="SDRA_AGENT_USER"
export SDRA_SAP_PASSWORD="your_password"
export SDRA_ACTION_MODE="APPROVAL_ONLY"
python ./src/sdra_ui_server.py
```

Open:

```text
http://127.0.0.1:8010
```


