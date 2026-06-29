const apiBase = "http://localhost:8001";
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
const emailPreview = document.getElementById("email-preview");
const previewSubject = document.getElementById("preview-subject");
const previewBody = document.getElementById("preview-body");
const previewWhySend = document.getElementById("preview-why-send");
const previewMajorIssue = document.getElementById("preview-major-issue");
const sendEmailButton = document.getElementById("send-email-button");
const regenerateButton = document.getElementById("regenerate-button");
const previewRecipientInput = document.getElementById("preview-recipient-input");
const previewSenderInput = document.getElementById("preview-sender-input");

let currentResult = null;
let currentOutreach = null;
let currentCanSend = false;

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

function isValidEmail(email) {
  return (
    typeof email === "string" &&
    email.trim() !== "" &&
    email.includes("@") &&
    !/^\s*N\/A\s*$/i.test(email)
  );
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatEmailBody(body) {
  if (!body) {
    return "<p>No draft available.</p>";
  }

  const escaped = escapeHtml(body.trim());
  return escaped
    .split(/\n{2,}/)
    .map((block) => `<p>${block.replace(/\n/g, "<br />")}</p>`)
    .join("");
}

function buildEmailDraft(result, draft) {
  let body = String(draft || "").trim();
  if (!body) {
    body = "I wanted to share a concise compliance review of the current risk outlook and recommended next steps.";
  }

  const recipientName = result.cso_name ? result.cso_name.split(" ")[0] : "";
  if (!/^(dear|hello|hi)\b/i.test(body)) {
    body = `${recipientName ? `Dear ${recipientName},\n\n` : "Hello,\n\n"}${body}`;
  }

  if (!/(best regards|regards|sincerely|thanks|thank you)/i.test(body)) {
    body = `${body}\n\nBest regards,\n[Your Name]\n[Your Company]`;
  }

  return body;
}

function updateSendButtonState() {
  const recipient = previewRecipientInput.value.trim();
  const validRecipient = isValidEmail(recipient);

  if (!currentCanSend) {
    sendEmailButton.disabled = true;
    sendEmailButton.textContent = "Not eligible to send";
    return;
  }

  if (!validRecipient) {
    sendEmailButton.disabled = true;
    sendEmailButton.textContent = "Enter a valid recipient";
    return;
  }

  sendEmailButton.disabled = false;
  sendEmailButton.textContent = "Send Email";
}

function createResultField(title, value) {
  const wrapper = document.createElement("div");
  wrapper.className = "result-item";
  wrapper.innerHTML = `<strong>${title}</strong><div>${value || "N/A"}</div>`;
  return wrapper;
}

function formatMetricValue(value, unit) {
  const metricValue = value || "N/A";
  const metricUnit = unit ? ` ${unit}` : "";
  return `${metricValue}${metricUnit}`;
}

function getComplianceBadge(status) {
  const normalizedStatus = (status || "N/A").toUpperCase();
  let background = "#e0f2fe";
  let color = "#0c4a6e";

  if (normalizedStatus === "COMPLIANT") {
    background = "#dcfce7";
    color = "#166534";
  } else if (normalizedStatus === "NON-COMPLIANT") {
    background = "#fee2e2";
    color = "#991b1b";
  } else if (normalizedStatus === "COMPLIANCE OPAQUE - AUDIT REQUIRED") {
    background = "#fef3c7";
    color = "#92400e";
  }

  return `<span style="display:inline-block;padding:0.25rem 0.6rem;border-radius:999px;font-size:0.9rem;font-weight:600;background:${background};color:${color};">${normalizedStatus}</span>`;
}

function renderResult(data) {
  resultSummary.innerHTML = "";
  resultDetails.innerHTML = "";
  resultSection.classList.remove("hidden");

  const result = data.result;
  const alreadyNotified = data.already_notified;
  currentResult = result;

  const metricName = data.primary_metric_name || result.primary_metric_name || "Metric";
  const metricValue = data.extracted_metric_value || result.extracted_metric_value || "N/A";
  const metricUnit = data.metric_unit || result.metric_unit || "";
  const targetValue = data.numeric_target || result.numeric_target || "N/A";
  const targetType = data.target_type || result.target_type || "Target";
  const complianceStatus = data.compliance_status || result.compliance_status || "N/A";
  const auditReasoning = data.audit_reasoning || result.audit_reasoning || "N/A";
  const outreachDraft = result.final_outreach_draft || "N/A";

  currentCanSend = Boolean(data.should_send_email);
  currentOutreach = currentCanSend
    ? {
        subject: result.discovered_company
          ? `Compliance review: ${result.discovered_company}`
          : "Compliance risk review",
        body: buildEmailDraft(result, outreachDraft),
      }
    : null;

  resultSummary.appendChild(createResultField("Company", result.discovered_company));
  resultSummary.appendChild(createResultField(metricName, formatMetricValue(metricValue, metricUnit)));
  resultSummary.appendChild(createResultField("Target", `${targetValue}${targetType ? ` (${targetType})` : ""}`));
  resultSummary.appendChild(createResultField("Compliance Status", getComplianceBadge(complianceStatus)));
  resultSummary.appendChild(createResultField("Audit Reasoning", auditReasoning));
  resultSummary.appendChild(createResultField("Contact", `${result.cso_name || "N/A"} • ${result.email || "N/A"}`));

  const detailsContainer = document.createElement("div");
  detailsContainer.className = "result-grid";
  detailsContainer.appendChild(createResultField("Region", result.target_region));
  detailsContainer.appendChild(createResultField("Sector", result.target_sector));
  detailsContainer.appendChild(createResultField("CSO Name", result.cso_name));
  detailsContainer.appendChild(createResultField("Designation", result.designation));
  detailsContainer.appendChild(createResultField("Email", result.email));
  detailsContainer.appendChild(createResultField("Regulatory Findings", result.raw_laws_text));
  detailsContainer.appendChild(createResultField("Outreach Draft", outreachDraft));
  resultDetails.appendChild(detailsContainer);

  if (currentCanSend) {
    emailPreview.classList.remove("hidden");
    previewSubject.textContent = currentOutreach.subject;
    previewBody.innerHTML = formatEmailBody(currentOutreach.body);
    previewWhySend.textContent = result.compliance_status
      ? `The compliance status is ${result.compliance_status}. This outreach is recommended because the prospect needs follow-up.`
      : "This outreach is recommended because the prospect needs follow-up.";
    previewMajorIssue.textContent = result.raw_laws_text || result.audit_reasoning || "N/A";
    previewRecipientInput.value = result.email || "";
    previewSenderInput.value = "";
    updateSendButtonState();
  } else {
    emailPreview.classList.add("hidden");
    currentOutreach = null;
    sendEmailButton.disabled = true;
    sendEmailButton.textContent = "Not eligible to send";
  }

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

async function sendEmail() {
  const recipient = previewRecipientInput.value.trim();
  const sender = previewSenderInput.value.trim();

  if (!currentOutreach) {
    setStatus("No email draft available.", "error");
    return;
  }

  if (!isValidEmail(recipient)) {
    setStatus("Please enter a valid recipient email.", "error");
    return;
  }

  sendEmailButton.disabled = true;
  sendEmailButton.textContent = "Sending...";

  const payload = {
    recipient,
    subject: currentOutreach.subject,
    body: currentOutreach.body,
  };

  if (sender) {
    payload.sender = sender;
  }

  try {
    const response = await fetch(`${apiBase}/api/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Unable to send email");
    }

    setStatus("✅ Email sent successfully.");
    sendEmailButton.textContent = "Send Email";
    sendEmailButton.disabled = false;
  } catch (error) {
    setStatus(error.message, "error");
    sendEmailButton.textContent = "Send Email";
    sendEmailButton.disabled = false;
  }
}

async function regenerateEmail() {
  if (!currentResult) {
    return;
  }

  setStatus("Regenerating outreach email... ");
  regenerateButton.disabled = true;
  regenerateButton.textContent = "Regenerating...";

  try {
    const response = await fetch(`${apiBase}/api/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        region: currentResult.target_region,
        sector: currentResult.target_sector,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Server error");
    }

    const data = await response.json();
    renderResult(data);
    regenerateButton.disabled = false;
    regenerateButton.textContent = "Regenerate Email";
    clearStatus();
  } catch (error) {
    setStatus(error.message, "error");
    regenerateButton.disabled = false;
    regenerateButton.textContent = "Regenerate Email";
  }
}

function toggleResultDetails() {
  const isHidden = resultDetails.classList.contains("hidden");
  resultDetails.classList.toggle("hidden");
  toggleDetailsButton.textContent = isHidden ? "Hide details" : "Show details";
}

previewRecipientInput.addEventListener("input", updateSendButtonState);
previewSenderInput.addEventListener("input", updateSendButtonState);

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
sendEmailButton.addEventListener("click", sendEmail);
regenerateButton.addEventListener("click", regenerateEmail);
loadHistory();
