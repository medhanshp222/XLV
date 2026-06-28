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
	} else if (normalizedStatus === "NO STATUTORY MANDATE") {
		background = "#f3e8ff";
		color = "#6b21a8";
	}

	return `<span style="display:inline-block;padding:0.25rem 0.6rem;border-radius:999px;font-size:0.9rem;font-weight:600;background:${background};color:${color};">${normalizedStatus}</span>`;
}

function renderMetricScorecard(metrics) {
	const scorecardWrapper = document.createElement("div");
	scorecardWrapper.className = "scorecard-wrapper";

	const table = document.createElement("table");
	table.className = "scorecard-table";

	table.innerHTML = `
		<thead>
			<tr>
				<th>Metric</th>
				<th>Value</th>
				<th>Unit</th>
				<th>Status</th>
			</tr>
		</thead>
	`;

	const tbody = document.createElement("tbody");
	(metrics || []).forEach((metric) => {
		if (!metric || typeof metric !== "object") {
			return;
		}

		const metricName = metric.metric_name || "N/A";
		const metricValue = metric.extracted_metric_value || "N/A";
		const metricUnit = metric.metric_unit || "N/A";
		const normalizedStatus = metricValue && metricValue !== "N/A"
			? "COMPLIANT"
			: "COMPLIANCE OPAQUE - AUDIT REQUIRED";

		const row = document.createElement("tr");
		row.innerHTML = `
			<td>${metricName}</td>
			<td>${metricValue}</td>
			<td>${metricUnit}</td>
			<td>${getComplianceBadge(normalizedStatus)}</td>
		`;
		tbody.appendChild(row);
	});

	table.appendChild(tbody);
	scorecardWrapper.appendChild(table);
	resultSummary.appendChild(scorecardWrapper);
}

function renderResult(data) {
	resultSummary.innerHTML = "";
	resultDetails.innerHTML = "";
	resultSection.classList.remove("hidden");

	const result = data.result;
	const alreadyNotified = data.already_notified;
	currentResult = result;

	renderMetricScorecard(data.metrics || result.metric_results || []);

	const complianceStatus = data.compliance_status || result.compliance_status || "N/A";
	const auditReasoning = data.audit_reasoning || result.audit_reasoning || "N/A";

	const summaryMeta = document.createElement("div");
	summaryMeta.className = "summary-meta";
	summaryMeta.appendChild(createResultField("Company", result.discovered_company));
	summaryMeta.appendChild(createResultField("Compliance Status", getComplianceBadge(complianceStatus)));
	summaryMeta.appendChild(createResultField("Audit Reasoning", auditReasoning));
	resultSummary.appendChild(summaryMeta);

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