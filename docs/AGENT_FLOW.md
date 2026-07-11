# Agent Flow

The agent follows a practical observe-analyze-decide-act-monitor pattern.

## Agentic Flow

```mermaid
flowchart TD
    A["Observe open sales orders from SAP"]
    B["Analyze stock, blocks, delivery status, and delivery date"]
    C["Decide readiness status and priority"]
    D["Choose action: approval request, follow-up, monitor, or no action"]
    E["Write approval/action result"]
    F["Show decision, reason, and next step in UI"]
    G["Human reviews or approves controlled action"]
    H["Run again to confirm dispatch readiness"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> A
```

## Decision Examples

| Situation | Agent Decision | Next Step |
|---|---|---|
| Confirmed stock and no blocks | Ready for delivery | Create approval request |
| Credit block | Blocked | Ask credit team to release block |
| Delivery block | Blocked | Resolve delivery block in sales order |
| Stock shortage | At risk | Follow up with supply planning |
| Existing delivery found | Already in delivery | Monitor PGI status |

## Action Modes

| Mode | Behavior |
|---|---|
| `APPROVAL_ONLY` | Agent creates approval/follow-up records but does not directly create delivery |
| `CONTROLLED_AUTONOMY` | Agent can execute controlled actions after required approvals are present |
