const statusPill = document.querySelector("#statusPill");
const connectionState = document.querySelector("#connectionState");
const authState = document.querySelector("#authState");
const actionMode = document.querySelector("#actionMode");
const lastRun = document.querySelector("#lastRun");
const messageBox = document.querySelector("#messageBox");
const decisionRows = document.querySelector("#decisionRows");
const actionList = document.querySelector("#actionList");
const runForm = document.querySelector("#runForm");
const orderSearch = document.querySelector("#orderSearch");
const statusFilter = document.querySelector("#statusFilter");
const clearFilters = document.querySelector("#clearFilters");
const resultCount = document.querySelector("#resultCount");
const orderDetail = document.querySelector("#orderDetail");

let currentDecisions = [];
let currentActions = [];

const today = new Date().toISOString().slice(0, 10);
runForm.elements.planning_date.value = today;

document.querySelector("#checkConfig").addEventListener("click", checkFormConfig);
document.querySelector("#refreshStatus").addEventListener("click", checkStatus);
runForm.addEventListener("submit", runAgent);
orderSearch.addEventListener("input", renderFilteredResults);
statusFilter.addEventListener("change", renderFilteredResults);
clearFilters.addEventListener("click", clearResultFilters);
decisionRows.addEventListener("click", showOrderFromTable);

checkStatus();

async function checkStatus() {
  setBusy("Checking");
  try {
    const response = await fetch("/api/status");
    const payload = await response.json();
    renderStatus(payload);
  } catch (error) {
    renderError(`Could not check the server: ${error.message}`);
  }
}

async function checkFormConfig() {
  setBusy("Checking");
  const formData = new FormData(runForm);
  const payload = Object.fromEntries(formData.entries());
  payload.auth_mode = "BASIC";
  payload.sap_bearer_token = "";

  const missingFields = requiredFormFields(payload);
  if (missingFields.length) {
    renderError(`Please fill: ${missingFields.join(", ")}`);
    return;
  }

  messageBox.className = "message-box";
  messageBox.textContent = "Checking the SAP details entered on this screen.";

  try {
    const response = await fetch("/api/check-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    renderStatus(result);
  } catch (error) {
    renderError(`Could not check the connection: ${error.message}`);
  }
}

async function runAgent(event) {
  event.preventDefault();
  setBusy("Running");
  messageBox.className = "message-box";
  messageBox.textContent = "Checking SAP and preparing the dispatch list.";
  const formData = new FormData(runForm);
  const payload = Object.fromEntries(formData.entries());
  payload.auth_mode = "BASIC";
  payload.sap_bearer_token = "";

  const missingFields = requiredFormFields(payload);
  if (missingFields.length) {
    renderError(`Please fill: ${missingFields.join(", ")}`);
    return;
  }

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!result.ok) {
      renderError(result.message || result.status || "The dispatch check failed.");
      if (result.missing_environment_variables) {
        messageBox.textContent += ` Missing: ${result.missing_environment_variables.join(", ")}`;
      }
      return;
    }
    renderRun(result.result);
  } catch (error) {
    renderError(`The dispatch check failed: ${error.message}`);
  }
}

function renderStatus(payload) {
  const ready = payload.status === "READY";
  statusPill.textContent = ready ? "Ready" : "Needs setup";
  statusPill.className = `status-pill ${ready ? "ready" : "error"}`;
  connectionState.textContent = payload.sap_base_url_configured ? "Ready" : "Missing";
  authState.textContent = friendlyAuth(payload.auth_mode);
  actionMode.textContent = friendlyMode(payload.action_mode);
  messageBox.className = `message-box ${ready ? "success" : ""}`;
  messageBox.textContent = ready
    ? "SAP details look complete. You can run the dispatch check now."
    : `Please add: ${payload.missing_environment_variables.join(", ")}`;
}

function renderRun(result) {
  statusPill.textContent = "Done";
  statusPill.className = "status-pill ready";
  lastRun.textContent = result.run_id;
  messageBox.className = "message-box success";
  messageBox.textContent = `Checked ${result.evaluated_order_lines} sales order line(s).`;
  currentDecisions = result.decisions || [];
  currentActions = result.action_results || [];
  renderFilteredResults();
}

function renderFilteredResults() {
  const searchText = orderSearch.value.trim().toLowerCase();
  const selectedStatus = statusFilter.value;
  const filtered = currentDecisions.filter((decision) => {
    const order = decision.order || {};
    const haystack = [
      order.sales_order,
      order.sales_order_item,
      order.customer_name,
      order.customer_id,
      order.material,
      order.material_description,
      order.plant,
      decision.reason_code,
      friendlyReason(decision.reason_code),
      friendlyStatus(decision.readiness_status),
    ].join(" ").toLowerCase();
    const matchesSearch = !searchText || haystack.includes(searchText);
    const matchesStatus = !selectedStatus || decision.readiness_status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  renderDecisions(filtered);
  renderFilteredActions(searchText);
  resultCount.textContent = currentDecisions.length
    ? `${filtered.length} of ${currentDecisions.length} order line(s) shown`
    : "No run yet.";
  if (!filtered.length) {
    orderDetail.textContent = currentDecisions.length
      ? "No order matches this search. Clear filters or try another sales order, customer, or material."
      : "Select an order to see the action needed.";
  }
}

function renderDecisions(decisions) {
  if (!decisions.length) {
    decisionRows.innerHTML = '<tr><td colspan="8" class="empty-state">No matching sales orders found.</td></tr>';
    return;
  }

  decisionRows.innerHTML = decisions.map((decision) => {
    const order = decision.order;
    const originalIndex = currentDecisions.indexOf(decision);
    return `
      <tr>
        <td>${escapeHtml(decision.priority_rank)}</td>
        <td>${escapeHtml(order.sales_order)} / ${escapeHtml(order.sales_order_item)}</td>
        <td>${escapeHtml(order.customer_name)}</td>
        <td>${escapeHtml(order.material)}</td>
        <td><span class="tag ${statusClass(decision.readiness_status)}">${escapeHtml(friendlyStatus(decision.readiness_status))}</span></td>
        <td>${escapeHtml(decision.dispatch_qty)}</td>
        <td>${escapeHtml(friendlyShortReason(decision.reason_code))}</td>
        <td><button type="button" class="link-button" data-decision-index="${originalIndex}">View</button></td>
      </tr>
    `;
  }).join("");
}

function renderActions(actions) {
  if (!actions.length) {
    actionList.innerHTML = '<div class="empty-state">No SAP actions were needed.</div>';
    return;
  }

  actionList.innerHTML = actions.map((action) => `
    <div class="action-item">
      <div>
        <div class="action-title-row">
          <strong>${escapeHtml(friendlyAction(action.action_name))}</strong>
          <span class="order-ref">${escapeHtml(action.sales_order || "-")} / ${escapeHtml(action.sales_order_item || "-")}</span>
        </div>
        <p class="action-subtitle">${escapeHtml(action.customer_name || "-")} - ${escapeHtml(action.material || "-")} - ${escapeHtml(action.dispatch_qty || "0")} ${escapeHtml(action.uom || "")}</p>
        <dl class="action-details">
          <div>
            <dt>SAP message</dt>
            <dd>${escapeHtml(action.message || "Action recorded.")}</dd>
          </div>
          <div>
            <dt>Reason</dt>
            <dd>${escapeHtml(friendlyReason(action.reason_code))}</dd>
          </div>
          <div class="next-step">
            <dt>Next step</dt>
            <dd>${escapeHtml(action.next_step || "Review this item in SAP.")}</dd>
          </div>
        </dl>
      </div>
      <span class="tag ${action.status === "SUCCESS" ? "ready" : "monitor"}">${escapeHtml(friendlyResult(action.status))}</span>
    </div>
  `).join("");
}

function clearResultFilters() {
  orderSearch.value = "";
  statusFilter.value = "";
  renderFilteredResults();
}

function showOrderFromTable(event) {
  const button = event.target.closest("[data-decision-index]");
  if (!button) return;
  const decision = currentDecisions[Number(button.dataset.decisionIndex)];
  if (!decision) return;
  renderOrderDetail(decision);
}

function renderOrderDetail(decision) {
  const order = decision.order || {};
  const action = currentActions.find((item) =>
    item.sales_order === order.sales_order && item.sales_order_item === order.sales_order_item
  );
  const nextStep = action?.next_step || nextStepForDecision(decision);
  orderDetail.innerHTML = `
    <div class="detail-title-row">
      <strong>${escapeHtml(order.sales_order || "-")} / ${escapeHtml(order.sales_order_item || "-")}</strong>
      <span class="tag ${statusClass(decision.readiness_status)}">${escapeHtml(friendlyStatus(decision.readiness_status))}</span>
    </div>
    <div class="detail-grid">
      <div><span>Customer</span><strong>${escapeHtml(order.customer_name || "-")}</strong></div>
      <div><span>Material</span><strong>${escapeHtml(order.material || "-")}</strong></div>
      <div><span>Plant</span><strong>${escapeHtml(order.plant || "-")}</strong></div>
      <div><span>Qty</span><strong>${escapeHtml(decision.dispatch_qty)} ${escapeHtml(order.sales_unit || "")}</strong></div>
    </div>
    <p><b>Reason:</b> ${escapeHtml(friendlyReason(decision.reason_code))}</p>
    <p><b>Next step:</b> ${escapeHtml(nextStep)}</p>
  `;
}

function renderFilteredActions(searchText) {
  if (!searchText || !currentActions.length) {
    renderActions(currentActions);
    return;
  }
  const matchingActions = currentActions.filter((action) =>
    [action.sales_order, action.sales_order_item, action.customer_name, action.material, action.reason_code]
      .join(" ")
      .toLowerCase()
      .includes(searchText)
  );
  renderActions(matchingActions);
}

function renderError(message) {
  statusPill.textContent = "Check needed";
  statusPill.className = "status-pill error";
  messageBox.className = "message-box error";
  messageBox.textContent = message;
}

function setBusy(label) {
  statusPill.textContent = label;
  statusPill.className = "status-pill";
}

function requiredFormFields(payload) {
  const labels = [];
  if (!payload.sap_base_url) labels.push("SAP system URL");
  if (!payload.sap_client) labels.push("Client");
  if (!payload.sap_username) labels.push("SAP user");
  if (!payload.sap_password) labels.push("SAP password");
  if (!payload.planning_date) labels.push("Dispatch date");
  return labels;
}

function friendlyAuth(value) {
  if (value === "BASIC") return "User/password";
  if (value === "BEARER") return "Token";
  if (value === "DESTINATION") return "Destination";
  return value || "-";
}

function friendlyMode(value) {
  if (value === "APPROVAL_ONLY") return "Ask first";
  if (value === "CONTROLLED_AUTONOMY") return "After approval";
  return value || "-";
}

function friendlyStatus(value) {
  const labels = {
    READY_FOR_DELIVERY: "Ready",
    PARTIALLY_READY: "Partial stock",
    BLOCKED: "Blocked",
    AT_RISK: "At risk",
    ALREADY_IN_DELIVERY: "Already in delivery",
    NOT_DUE_FOR_DISPATCH: "Not due today",
  };
  return labels[value] || value || "-";
}

function friendlyAction(value) {
  const labels = {
    SDRA_ACTION_REQUEST_DELIVERY_APPROVAL: "Approval request",
    SDRA_ACTION_CREATE_OUTBOUND_DELIVERY: "Delivery creation",
    SDRA_ACTION_ESCALATE_BLOCKED_ORDER: "Blocked order follow-up",
    SDRA_ACTION_MONITOR_PGI_STATUS: "Existing delivery check",
  };
  return labels[value] || value || "SAP action";
}

function friendlyReason(value) {
  const labels = {
    SDRA_REASON_READY_CLEAN: "Stock is confirmed and order is ready for dispatch approval.",
    SDRA_REASON_CREDIT_BLOCK: "Sales order has a credit block.",
    SDRA_REASON_DELIVERY_BLOCK: "Sales order has a delivery block.",
    SDRA_REASON_BILLING_BLOCK: "Sales order has a billing block.",
    SDRA_REASON_PARTIAL_STOCK: "Only partial quantity is available.",
    SDRA_REASON_NO_STOCK: "Required stock is not available.",
    SDRA_REASON_EXISTING_DELIVERY: "A delivery already exists for this order line.",
    SDRA_REASON_NOT_DUE: "Requested delivery date is not due today.",
  };
  return labels[value] || value || "-";
}

function friendlyShortReason(value) {
  const labels = {
    SDRA_REASON_READY_CLEAN: "Ready clean",
    SDRA_REASON_CREDIT_BLOCK: "Credit block",
    SDRA_REASON_DELIVERY_BLOCK: "Delivery block",
    SDRA_REASON_BILLING_BLOCK: "Billing block",
    SDRA_REASON_PARTIAL_STOCK: "Partial stock",
    SDRA_REASON_NO_STOCK: "No stock",
    SDRA_REASON_EXISTING_DELIVERY: "Existing delivery",
    SDRA_REASON_NOT_DUE: "Not due",
  };
  return labels[value] || value || "-";
}

function nextStepForDecision(decision) {
  if (decision.recommended_action === "SDRA_ACTION_REQUEST_DELIVERY_APPROVAL") {
    return "Approve the request in ZSDRA_APPR_REQ, then run delivery creation.";
  }
  if (decision.recommended_action === "SDRA_ACTION_ESCALATE_BLOCKED_ORDER") {
    return "Clear the block or stock issue with the owner team, then rerun the dispatch check.";
  }
  if (decision.recommended_action === "SDRA_ACTION_MONITOR_PGI_STATUS") {
    return "Check the existing delivery and PGI status in SAP.";
  }
  return "Review this order line in SAP and rerun the dispatch check after fixing it.";
}

function friendlyResult(value) {
  const labels = {
    SUCCESS: "Done",
    FAILED: "Failed",
    LOGGED: "Logged",
    SKIPPED_APPROVAL_REQUIRED: "Approval needed",
    SKIPPED_NOT_IMPLEMENTED: "Not active yet",
  };
  return labels[value] || value || "-";
}

function statusClass(status) {
  if (status === "READY_FOR_DELIVERY") return "ready";
  if (status === "PARTIALLY_READY") return "partial";
  if (status === "BLOCKED") return "blocked";
  if (status === "AT_RISK") return "risk";
  return "monitor";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
