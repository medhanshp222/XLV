const apiBase = "http://localhost:8000";
const form = document.getElementById("search-form");
const regionInput = document.getElementById("region-input");
const sectorInput = document.getElementById("sector-input");
const statusBar = document.getElementById("status");
const resultSection = document.getElementById("result-section");
const resultSummary = document.getElementById("result-summary");
const resultDetails = document.getElementById("result-details");
const toggleDetailsButton = document.getElementById("toggle-details-button");
const actionRow = document.getElementById("action-row");
const approveButton = document.getElementById("approve-button");
const historySection = document.getElementById("history-section");
const historyContent = document.getElementById("history-content");

let currentResult = null;

function setStatus(message, type = "info") {
  statusBar.textContent = message;
  statusBar.className = "status visible";
  if (type === "error") {
    statusBar.style.background = "#fee2e2";
    statusBar.style.color = "#991b1b";
  } else {
    statusBar.style.background = "#e0f2fe";
    statusBar.style.color = "#0c4a6e";
  }
}

function clearStatus() {
  statusBar.textContent = "";
  statusBar.className = "status";
}

function createResultField(title, value) {
  const wrapper = document.createElement("div");
  wrapper.className = "result-item";
  wrapper.innerHTML = `<strong>${title}</strong><div>${value || "N/A"}</div>`;
  return wrapper;
}

function renderResult(data) {
  resultSummary.innerHTML = "";
  resultDetails.innerHTML = "";
  resultSection.classList.remove("hidden");

  const result = data.result;
  const alreadyNotified = data.already_notified;
  currentResult = result;

  resultSummary.appendChild(createResultField("Company", result.discovered_company));
  resultSummary.appendChild(createResultField("Emission Metric", result.company_emission_metric));
  resultSummary.appendChild(createResultField("Compliance Status", result.compliance_status));
  resultSummary.appendChild(createResultField("Audit Reasoning", result.audit_reasoning));
  resultSummary.appendChild(createResultField("Contact", `${result.cso_name || "N/A"} • ${result.email || "N/A"}`));

  const detailsContainer = document.createElement("div");
  detailsContainer.className = "result-grid";
  detailsContainer.appendChild(createResultField("Region", result.target_region));
  detailsContainer.appendChild(createResultField("Sector", result.target_sector));
  detailsContainer.appendChild(createResultField("CSO Name", result.cso_name));
  detailsContainer.appendChild(createResultField("Designation", result.designation));
  detailsContainer.appendChild(createResultField("Email", result.email));
  detailsContainer.appendChild(createResultField("Regulatory Findings", result.raw_laws_text));
  detailsContainer.appendChild(createResultField("Outreach Draft", result.final_outreach_draft));
  resultDetails.appendChild(detailsContainer);

  toggleDetailsButton.textContent = "Show details";
  resultDetails.classList.add("hidden");

  if (alreadyNotified) {
    actionRow.classList.remove("hidden");
    approveButton.textContent = "Already notified — no action needed";
    approveButton.disabled = true;
    setStatus("This company has already been approved and recorded.");
  } else {
    actionRow.classList.remove("hidden");
    approveButton.textContent = "Approve & Save Notification";
    approveButton.disabled = false;
    clearStatus();
  }
}

function toggleResultDetails() {
  const isHidden = resultDetails.classList.contains("hidden");
  resultDetails.classList.toggle("hidden");
  toggleDetailsButton.textContent = isHidden ? "Hide details" : "Show details";
}

function renderNotifications(notifications) {
  historyContent.innerHTML = "";
  if (!notifications.length) {
    historySection.classList.add("hidden");
    return;
  }
  historySection.classList.remove("hidden");

  notifications.forEach((notification) => {
    const item = document.createElement("div");
    item.className = "notification-hit";
    item.innerHTML = `
      <strong>${notification.company}</strong>
      <div><strong>Region:</strong> ${notification.region}</div>
      <div><strong>Sector:</strong> ${notification.sector}</div>
      <div><strong>Email:</strong> ${notification.email || "N/A"}</div>
      <div><strong>Saved:</strong> ${notification.notified_at}</div>
      <div><strong>Source:</strong> ${notification.source}</div>
    `;
    historyContent.appendChild(item);
  });
}

async function loadHistory() {
  try {
    const response = await fetch(`${apiBase}/api/notifications`);
    const notifications = await response.json();
    renderNotifications(notifications);
  } catch (error) {
    setStatus("Unable to load notification history.", "error");
  }
}

async function runSearch(event) {
  event.preventDefault();
  clearStatus();
  resultSection.classList.add("hidden");
  actionRow.classList.add("hidden");

  const region = regionInput.value.trim();
  const sector = sectorInput.value.trim();
  if (!region || !sector) {
    setStatus("Please enter both region and sector.", "error");
    return;
  }

  setStatus("Running search and compliance pipeline...");

  try {
    const response = await fetch(`${apiBase}/api/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ region, sector }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Server error");
    }

    const data = await response.json();
    renderResult(data);
    if (data.already_notified) {
      renderNotifications([data.notification]);
    }
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function approveNotification() {
  if (!currentResult) {
    return;
  }
  const payload = {
    region: currentResult.target_region,
    sector: currentResult.target_sector,
    company: currentResult.discovered_company,
    email: currentResult.email,
    message: currentResult.final_outreach_draft,
    source: "frontend_approval",
  };

  approveButton.disabled = true;
  approveButton.textContent = "Saving...";

  try {
    const response = await fetch(`${apiBase}/api/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Unable to save notification");
    }
    const result = await response.json();
    setStatus("Notification saved successfully.");
    loadHistory();
    approveButton.textContent = "Already notified — no action needed";
    approveButton.disabled = true;
  } catch (error) {
    setStatus(error.message, "error");
    approveButton.disabled = false;
    approveButton.textContent = "Approve & Save Notification";
  }
}

form.addEventListener("submit", runSearch);
approveButton.addEventListener("click", approveNotification);
toggleDetailsButton.addEventListener("click", toggleResultDetails);
loadHistory();
