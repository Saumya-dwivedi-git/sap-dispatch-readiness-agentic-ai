# Security and Demo Notes

This repository is intended as a portfolio/demo version of the SAP Dispatch Readiness Agentic AI prototype.

## Do Not Commit

- Real SAP passwords
- Real SAP system URLs
- SAP client-specific confidential data
- Runtime logs from `run_outputs/`
- Screenshots showing passwords, private hostnames, customer-sensitive records, or internal tickets
- Company/client code unless you have permission to share it

## Safe To Show

- Sanitized UI screenshots
- Architecture diagram
- Mock/sample payloads
- ABAP object names and high-level design
- Example configuration with placeholder hostnames
- Demo video where private data is blurred or masked

## Suggested Demo Story

1. Show the dispatch readiness UI.
2. Explain the observe-analyze-decide-act loop.
3. Show the Sales Orders filter/search.
4. Show a selected order with reason and next step.
5. Show the approval request concept in SAP.
6. Explain controlled autonomy: the agent can request approval first, then act after approval.

## Recommended Positioning

This is not a generic chatbot. It is an SAP action agent that connects to SAP OData/RFC-style wrappers, classifies dispatch readiness, and creates controlled business actions.
