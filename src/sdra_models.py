from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Dict


@dataclass
class SdraSalesOrderLine:
    sales_order: str
    sales_order_item: str
    customer_id: str
    customer_name: str
    customer_priority: str
    material: str
    material_description: str
    plant: str
    storage_location: str
    shipping_point: str
    requested_delivery_date: date
    order_qty: float
    confirmed_qty: float
    available_stock_qty: float
    sales_unit: str
    credit_block: bool
    delivery_block: bool
    billing_block: bool
    existing_delivery: bool
    delivery_cutoff_time: str


@dataclass
class SdraDecision:
    priority_rank: int
    priority_score: int
    readiness_status: str
    reason_code: str
    recommended_action: str
    approval_required: bool
    owner_team: str
    dispatch_qty: float
    order: SdraSalesOrderLine

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["approval_required"] = "YES" if self.approval_required else "NO"
        payload["order"]["requested_delivery_date"] = self.order.requested_delivery_date.isoformat()
        return payload


@dataclass
class SdraActionResult:
    action_name: str
    status: str
    sap_document: str
    message: str
