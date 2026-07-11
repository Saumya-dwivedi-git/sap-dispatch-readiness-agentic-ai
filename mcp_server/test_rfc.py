from sdra_sap_rfc_client import SdraSapRfcClient


def main():
    client = SdraSapRfcClient()
    result = client.create_approval_request({
        "approval_type": "SDRA_APPR_CREATE_FULL_DELIVERY",
        "sales_order": "50001234",
        "sales_order_item": "000010",
        "dispatch_qty": 1,
        "uom": "EA",
        "readiness_status": "READY_FOR_DELIVERY",
        "reason_code": "SDRA_REASON_READY_CLEAN",
        "owner_team": "Dispatch planner",
    })
    print(result)


if __name__ == "__main__":
    main()

