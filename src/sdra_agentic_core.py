from datetime import date, datetime
from typing import Any, Dict, List

from sdra_models import SdraDecision, SdraSalesOrderLine
from sdra_readiness_engine import SdraReadinessEngine


class SdraDispatchReadinessAgent:
    object_name = "SDRA_DISPATCH_READINESS_AGENT"

    def __init__(self, gateway, readiness_engine: SdraReadinessEngine):
        self.gateway = gateway
        self.readiness_engine = readiness_engine

    def run(self, planning_date: date, horizon_days: int) -> Dict[str, Any]:
        run_id = f"SDRA_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.gateway.write_action_log("SDRA_EVENT_DISPATCH_SCAN_STARTED", {
            "run_id": run_id,
            "planning_date": planning_date.isoformat(),
            "horizon_days": horizon_days,
        })

        observed_orders = self.observe(planning_date, horizon_days)
        decisions = self.analyze_and_decide(observed_orders, planning_date)
        action_results = self.act(decisions)

        self.gateway.write_action_log("SDRA_EVENT_RUN_COMPLETED", {
            "run_id": run_id,
            "evaluated_order_lines": len(decisions),
            "action_results": action_results,
        })

        return {
            "run_id": run_id,
            "evaluated_order_lines": len(decisions),
            "decisions": [decision.to_payload() for decision in decisions],
            "action_results": action_results,
        }

    def observe(self, planning_date: date, horizon_days: int) -> List[SdraSalesOrderLine]:
        sap_rows = self.gateway.fetch_open_sales_orders(planning_date.isoformat(), horizon_days)
        return [self._map_sap_order(row) for row in sap_rows]

    def analyze_and_decide(self, orders: List[SdraSalesOrderLine], planning_date: date) -> List[SdraDecision]:
        decisions = [self.readiness_engine.classify(order, planning_date) for order in orders]
        decisions.sort(key=lambda decision: decision.priority_score, reverse=True)
        for index, decision in enumerate(decisions, start=1):
            decision.priority_rank = index
            self.gateway.write_action_log("SDRA_EVENT_ORDER_CLASSIFIED", decision.to_payload())
        return decisions

    def act(self, decisions: List[SdraDecision]) -> List[Dict[str, Any]]:
        results = []
        for decision in decisions:
            result = None
            if decision.recommended_action == "SDRA_ACTION_REQUEST_DELIVERY_APPROVAL":
                result = self.gateway.create_approval_request(decision)
            elif decision.recommended_action == "SDRA_ACTION_ESCALATE_BLOCKED_ORDER":
                result = self.gateway.escalate_blocked_order(decision)
            elif decision.recommended_action == "SDRA_ACTION_MONITOR_PGI_STATUS":
                result = self.gateway.monitor_delivery(decision)
            if result:
                results.append(self._action_result_payload(result, decision))
        return results

    def _action_result_payload(self, result, decision: SdraDecision) -> Dict[str, Any]:
        if isinstance(result, dict):
            payload = result.copy()
        else:
            payload = {
                "action_name": getattr(result, "action_name", ""),
                "status": getattr(result, "status", ""),
                "sap_document": getattr(result, "sap_document", ""),
                "message": getattr(result, "message", ""),
            }
        action_name = str(payload.get("action_name") or "")
        status = str(payload.get("status") or "")
        payload.update({
            "sales_order": decision.order.sales_order,
            "sales_order_item": decision.order.sales_order_item,
            "customer_name": decision.order.customer_name,
            "material": decision.order.material,
            "dispatch_qty": decision.dispatch_qty,
            "uom": decision.order.sales_unit,
            "readiness_status": decision.readiness_status,
            "reason_code": decision.reason_code,
            "owner_team": decision.owner_team,
            "next_step": self._next_step(action_name, status, decision),
        })
        return payload

    def _next_step(self, action_name: str, status: str, decision: SdraDecision) -> str:
        if status == "FAILED":
            return "Check the SAP error message, fix the master data or document issue, then run the dispatch check again."
        if action_name == "SDRA_ACTION_REQUEST_DELIVERY_APPROVAL":
            return "Open SE16N table ZSDRA_APPR_REQ, approve this request, then run the delivery creation step."
        if action_name == "SDRA_ACTION_ESCALATE_BLOCKED_ORDER":
            if decision.order.credit_block:
                return "Ask credit team to release the sales order credit block, then rerun the dispatch check."
            if decision.order.delivery_block:
                return "Remove or resolve the delivery block in the sales order, then rerun the dispatch check."
            if decision.order.billing_block:
                return "Review the billing block and confirm whether delivery can proceed."
            return "Review the blocked sales order with the owner team, clear the issue, then rerun the dispatch check."
        if action_name == "SDRA_ACTION_MONITOR_PGI_STATUS":
            return "Check the existing delivery and PGI status in SAP, then close the item if delivery is complete."
        return "Review this item in SAP and rerun the dispatch check after action is complete."

    def _map_sap_order(self, row: Dict[str, Any]) -> SdraSalesOrderLine:
        return SdraSalesOrderLine(
            sales_order=str(row.get("SalesOrder") or row.get("sales_order") or ""),
            sales_order_item=str(row.get("SalesOrderItem") or row.get("sales_order_item") or ""),
            customer_id=str(row.get("SoldToParty") or row.get("customer_id") or ""),
            customer_name=str(row.get("CustomerName") or row.get("customer_name") or ""),
            customer_priority=str(row.get("CustomerPriority") or row.get("customer_priority") or "NORMAL"),
            material=str(row.get("Material") or row.get("material") or ""),
            material_description=str(row.get("MaterialDescription") or row.get("material_description") or ""),
            plant=str(row.get("Plant") or row.get("plant") or ""),
            storage_location=str(row.get("StorageLocation") or row.get("storage_location") or ""),
            shipping_point=str(row.get("ShippingPoint") or row.get("shipping_point") or ""),
            requested_delivery_date=self._parse_date(row.get("RequestedDeliveryDate") or row.get("requested_delivery_date")),
            order_qty=self._number(row.get("OrderQuantity") or row.get("order_qty")),
            confirmed_qty=self._number(row.get("ConfirmedQuantity") or row.get("confirmed_qty")),
            available_stock_qty=self._number(row.get("AvailableStockQuantity") or row.get("available_stock_qty")),
            sales_unit=str(row.get("SalesUnit") or row.get("Uom") or row.get("uom") or "EA"),
            credit_block=self._bool(row.get("CreditBlock") or row.get("credit_block")),
            delivery_block=self._bool(row.get("DeliveryBlock") or row.get("delivery_block")),
            billing_block=self._bool(row.get("BillingBlock") or row.get("billing_block")),
            existing_delivery=self._bool(row.get("ExistingDelivery") or row.get("existing_delivery")),
            delivery_cutoff_time=str(row.get("DeliveryCutoffTime") or row.get("delivery_cutoff_time") or ""),
        )

    def _parse_date(self, value) -> date:
        if isinstance(value, date):
            return value
        text = str(value or "").replace("/Date(", "").replace(")/", "")
        if text.isdigit() and len(text) > 8:
            return datetime.fromtimestamp(int(text) / 1000).date()
        return datetime.strptime(text[:10], "%Y-%m-%d").date()

    def _number(self, value) -> float:
        try:
            return float(value or 0)
        except ValueError:
            return 0.0

    def _bool(self, value) -> bool:
        return str(value or "").strip().upper() in ("YES", "Y", "TRUE", "X", "1")
