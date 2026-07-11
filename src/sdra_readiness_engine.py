from datetime import date
from sdra_models import SdraDecision, SdraSalesOrderLine


SDRA_ACTION_REQUEST_DELIVERY_APPROVAL = "SDRA_ACTION_REQUEST_DELIVERY_APPROVAL"
SDRA_ACTION_CREATE_OUTBOUND_DELIVERY = "SDRA_ACTION_CREATE_OUTBOUND_DELIVERY"
SDRA_ACTION_ESCALATE_BLOCKED_ORDER = "SDRA_ACTION_ESCALATE_BLOCKED_ORDER"
SDRA_ACTION_MONITOR_PGI_STATUS = "SDRA_ACTION_MONITOR_PGI_STATUS"


class SdraReadinessEngine:
    object_name = "ZCL_SDRA_READINESS_ENGINE"

    def classify(self, order: SdraSalesOrderLine, planning_date: date) -> SdraDecision:
        status, reason, dispatch_qty, action, approval, owner = self._classify_order(order, planning_date)
        score = self._priority_score(order, planning_date, status)
        return SdraDecision(
            priority_rank=0,
            priority_score=score,
            readiness_status=status,
            reason_code=reason,
            recommended_action=action,
            approval_required=approval,
            owner_team=owner,
            dispatch_qty=dispatch_qty,
            order=order,
        )

    def _classify_order(self, order: SdraSalesOrderLine, planning_date: date):
        if order.existing_delivery:
            return "ALREADY_IN_DELIVERY", "SDRA_REASON_EXISTING_DELIVERY", 0, SDRA_ACTION_MONITOR_PGI_STATUS, False, "Warehouse or dispatch"

        if order.credit_block:
            return "BLOCKED", "SDRA_REASON_CREDIT_BLOCK", 0, SDRA_ACTION_ESCALATE_BLOCKED_ORDER, False, "Credit control"

        if order.delivery_block:
            return "BLOCKED", "SDRA_REASON_DELIVERY_BLOCK", 0, SDRA_ACTION_ESCALATE_BLOCKED_ORDER, False, "Sales or customer service"

        if order.billing_block:
            return "BLOCKED", "SDRA_REASON_BILLING_BLOCK", 0, SDRA_ACTION_ESCALATE_BLOCKED_ORDER, False, "Sales or finance"

        if not order.shipping_point:
            return "BLOCKED", "SDRA_REASON_MISSING_SHIPPING_POINT", 0, SDRA_ACTION_ESCALATE_BLOCKED_ORDER, False, "Master data or logistics"

        if order.requested_delivery_date > planning_date:
            return "NOT_DUE_FOR_DISPATCH", "SDRA_REASON_NOT_DUE_FOR_DISPATCH", 0, SDRA_ACTION_MONITOR_PGI_STATUS, False, "Dispatch planner"

        if order.confirmed_qty > 0 and order.available_stock_qty >= order.confirmed_qty:
            return "READY_FOR_DELIVERY", "SDRA_REASON_READY_CLEAN", order.confirmed_qty, SDRA_ACTION_REQUEST_DELIVERY_APPROVAL, True, "Dispatch planner"

        if 0 < order.available_stock_qty < order.confirmed_qty:
            return "PARTIALLY_READY", "SDRA_REASON_PARTIAL_STOCK", order.available_stock_qty, SDRA_ACTION_REQUEST_DELIVERY_APPROVAL, True, "Sales order manager"

        return "AT_RISK", "SDRA_REASON_NO_STOCK", 0, SDRA_ACTION_ESCALATE_BLOCKED_ORDER, False, "Supply planning"

    def _priority_score(self, order: SdraSalesOrderLine, planning_date: date, status: str) -> int:
        score = 0

        if order.requested_delivery_date < planning_date:
            score += 40
        elif order.requested_delivery_date == planning_date:
            score += 30

        if order.customer_priority.upper() == "HIGH":
            score += 25

        if order.confirmed_qty > 0 and order.available_stock_qty >= order.confirmed_qty:
            score += 20
        elif order.available_stock_qty > 0:
            score += 10

        if order.delivery_cutoff_time:
            score += 20

        if status in ("READY_FOR_DELIVERY", "PARTIALLY_READY", "AT_RISK"):
            score += 10
        elif status == "BLOCKED":
            score -= 50
        elif status == "ALREADY_IN_DELIVERY":
            score -= 20
        elif status == "NOT_DUE_FOR_DISPATCH":
            score -= 30

        return score
