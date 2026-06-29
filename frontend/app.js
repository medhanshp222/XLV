const apiBase = "";
const form = document.getElementById("search-form");
const regionInput = document.getElementById("region-input");
const sectorInput = document.getElementById("sector-input");
const statusBar = document.getElementById("status");
const resultSection = document.getElementById("result-section");
const resultSummary = document.getElementById("result-summary");
const resultDetails = document.getElementById("result-details");
const pdfSidebar = document.getElementById("pdf-sidebar");
const draftCard = document.getElementById("draft-card");
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
	const strong = document.createElement("strong");
	strong.textContent = title;
	const valueWrapper = document.createElement("div");
	if (typeof value === "string" && value.startsWith("<span")) {
		valueWrapper.innerHTML = value;
	} else {
		valueWrapper.textContent = value || "N/A";
	}
	wrapper.appendChild(strong);
	wrapper.appendChild(valueWrapper);
	return wrapper;
}

function createOverviewCard(title, content) {
	const card = document.createElement("div");
	card.className = "overview-card";

	const titleElement = document.createElement("div");
	titleElement.className = "overview-card-title";
	titleElement.textContent = title;

	const contentElement = document.createElement("div");
	contentElement.className = "overview-card-content";
	if (typeof content === "string" && content.startsWith("<span")) {
		contentElement.innerHTML = content;
	} else {
		contentElement.textContent = content || "N/A";
	}

	card.appendChild(titleElement);
	card.appendChild(contentElement);
	return card;
}

function escapeHtml(value) {
	const div = document.createElement("div");
	div.textContent = value || "";
	return div.innerHTML;
}

function renderPdfSidebar(result) {
	pdfSidebar.innerHTML = "";

	const pdfUrl = result.company_report_pdf_url || "";
	const sourcePages = result.company_report_source_pages || [];
	const pages = result.company_report_pages || [];

	const header = document.createElement("div");
	header.className = "pdf-sidebar-header";
	header.innerHTML = `
		<div>
			<p class="eyebrow">Downloaded report</p>
			<h3>${result.discovered_company || "Company report"}</h3>
		</div>
	`;
	pdfSidebar.appendChild(header);

	const meta = document.createElement("div");
	meta.className = "pdf-meta";
	meta.innerHTML = `
		<div><strong>Report URL</strong><div class="pdf-url-link">${pdfUrl ? `<a href="${escapeHtml(pdfUrl)}" target="_blank" rel="noreferrer">Open PDF source</a>` : "Not available"}</div></div>
		<div><strong>Loaded pages</strong><div>${pages.length}</div></div>
		<div><strong>Agent 2 source pages</strong><div>${sourcePages.length ? sourcePages.join(", ") : "None detected"}</div></div>
	`;
	pdfSidebar.appendChild(meta);

	const pagesLabel = document.createElement("div");
	pagesLabel.className = "pdf-section-title";
	pagesLabel.textContent = "Full extracted report text";
	pdfSidebar.appendChild(pagesLabel);

	const pagesContainer = document.createElement("div");
	pagesContainer.className = "pdf-pages";
	const pageMap = new Map();

	if (!pages.length) {
		const emptyState = document.createElement("div");
		emptyState.className = "result-item";
		emptyState.innerHTML = `<strong>No report pages available</strong><div>The PDF was not downloaded or its text could not be extracted.</div>`;
		pagesContainer.appendChild(emptyState);
	} else {
		pages.forEach((page) => {
			const pageCard = document.createElement("article");
			pageCard.className = "pdf-page";
			pageCard.id = `pdf-page-${page.page}`;
			const pageTitle = document.createElement("div");
			pageTitle.className = "pdf-page-number";
			pageTitle.textContent = `Page ${page.page}`;
			const pageText = document.createElement("pre");
			pageText.className = "pdf-page-text";
			pageText.textContent = page.text || "(No text extracted for this page)";
			pageCard.appendChild(pageTitle);
			pageCard.appendChild(pageText);
			pagesContainer.appendChild(pageCard);
			pageMap.set(page.page, pageCard);
		});
	}

	if (sourcePages.length) {
		const sourceChips = document.createElement("div");
		sourceChips.className = "pdf-chip-list";
		sourcePages.forEach((pageNumber) => {
			const chip = document.createElement("button");
			chip.type = "button";
			chip.className = "pdf-chip pdf-chip-button";
			chip.textContent = `Go to page ${pageNumber}`;
			chip.addEventListener("click", () => {
				const target = pageMap.get(pageNumber);
				if (target) {
					pagesContainer.querySelectorAll(".pdf-page").forEach((item) => item.classList.remove("pdf-page-active"));
					target.classList.add("pdf-page-active");
					target.scrollIntoView({ behavior: "smooth", block: "center" });
				}
			});
			sourceChips.appendChild(chip);
		});
		pdfSidebar.appendChild(sourceChips);
	}

	pdfSidebar.appendChild(pagesContainer);
}

function renderDraftCard(result) {
	draftCard.innerHTML = "";
	const draftText = result.final_outreach_draft || result.outreach_email || "";
	const gapValue = result.gap_calculation || result.gap || "N/A";
	const status = (result.compliance_status || "").toUpperCase();
	const gapDetected = gapValue && gapValue !== "0.00" && gapValue !== "N/A";
	const shouldShowDraft = draftText && (gapDetected || status === "NON-COMPLIANT");

	if (!shouldShowDraft) {
		draftCard.classList.add("hidden");
		return;
	}

	draftCard.classList.remove("hidden");
	draftCard.innerHTML = `
		<h3>Drafted outreach email</h3>
		<pre>${escapeHtml(draftText)}</pre>
		<div class="draft-note">Gap detected: ${escapeHtml(gapValue)}</div>
	`;
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

function deriveOpportunityInsight(result, metrics) {
	const status = (result.compliance_status || "N/A").toUpperCase();
	const foundMetricCount = (metrics || []).filter((metric) =>
		metric && metric.extracted_metric_value && metric.extracted_metric_value !== "N/A"
	).length;

	let baseScore = 50;
	let label = "Opportunity";
	let advice = "Use this insight to craft a targeted outreach message.";

	switch (status) {
		case "COMPLIANT":
			baseScore = 80;
			label = "Compliance strength";
			advice = "This company appears compliant. Position outreach as a partnership to accelerate sustainability leadership.";
			break;
		case "NON-COMPLIANT":
			baseScore = 30;
			label = "High priority";
			advice = "This company may face regulatory risk. Lead with an urgent, value-added compliance support offer.";
			break;
		case "COMPLIANCE OPAQUE - AUDIT REQUIRED":
			baseScore = 55;
			label = "Audit insight";
			advice = "Key data is missing. Suggest a rapid compliance review to clarify the gap and next steps.";
			break;
		case "NO STATUTORY MANDATE":
			baseScore = 65;
			label = "Early-stage prospect";
			advice = "No current mandate detected. Offer advisory support to move ahead of future regulation.";
			break;
	}

	const score = Math.min(100, baseScore + foundMetricCount * 10);
	return { score, label, advice, metricsFound: foundMetricCount };
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

	const overviewContainer = document.createElement("div");
	overviewContainer.className = "overview-panel";
	overviewContainer.appendChild(createOverviewCard("Company", result.discovered_company));
	overviewContainer.appendChild(createOverviewCard("Compliance Status", getComplianceBadge(complianceStatus)));
	overviewContainer.appendChild(createOverviewCard("Audit Reasoning", auditReasoning));
	resultSummary.appendChild(overviewContainer);

	const detailsContainer = document.createElement("div");
	detailsContainer.className = "result-grid";
	detailsContainer.appendChild(createResultField("Region", result.target_region));
	detailsContainer.appendChild(createResultField("Sector", result.target_sector));
	detailsContainer.appendChild(createResultField("Gap calculation", result.gap_calculation || "N/A"));
	detailsContainer.appendChild(createResultField("CSO Name", result.cso_name));
	detailsContainer.appendChild(createResultField("Designation", result.designation));
	detailsContainer.appendChild(createResultField("Email", result.email));
	detailsContainer.appendChild(createResultField("Regulatory Findings", result.raw_laws_text));
	resultDetails.appendChild(detailsContainer);

	const insightTarget = document.getElementById("insight-card");
	const insight = deriveOpportunityInsight(result, data.metrics || result.metric_results || []);
	insightTarget.className = "insight-card";
	insightTarget.innerHTML = `
		<div class="insight-header">
			<h3>${insight.label}</h3>
			<div class="insight-score">${insight.score}% chance of strong fit</div>
		</div>
		<div class="insight-meter"><span style="width:${insight.score}%"></span></div>
		<p>${insight.advice}</p>
		<div class="insight-chips">
			<div class="insight-chip">${insight.metricsFound} metric${insight.metricsFound === 1 ? "" : "s"} found</div>
			<div class="insight-chip">${result.discovered_company || "Company pending"}</div>
			<div class="insight-chip">${result.target_region} • ${result.target_sector}</div>
		</div>
	`;

	renderDraftCard(result);
	renderPdfSidebar(result);
	pdfSidebar.classList.remove("hidden");
	insightTarget.classList.remove("hidden");
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

async function parseJsonResponse(response) {
	const text = await response.text();
	if (!text) {
		return null;
	}
	try {
		return JSON.parse(text);
	} catch (parseError) {
		throw new Error(`Invalid JSON response: ${text}`);
	}
}

async function loadHistory() {
	try {
		const response = await fetch(`${apiBase}/api/notifications`);
		if (!response.ok) {
			const body = await response.text();
			throw new Error(`Notifications load failed (${response.status}): ${body}`);
		}
		const notifications = await parseJsonResponse(response) || [];
		renderNotifications(notifications);
	} catch (error) {
		setStatus(`Unable to load notification history: ${error.message}`, "error");
		console.error("Notification history error:", error);
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
			const body = await response.text();
			let details = body;
			try {
				const parsed = JSON.parse(body);
				details = parsed.detail || parsed.message || JSON.stringify(parsed);
			} catch (parseError) {
				// keep raw text if not valid JSON
			}
			throw new Error(details || `Server error (${response.status})`);
		}

		const data = await parseJsonResponse(response);
		if (!data) {
			throw new Error("Empty response from server.");
		}
		renderResult(data);
		if (data.already_notified) {
			renderNotifications([data.notification]);
		}
	} catch (error) {
		setStatus(`Search failed: ${error.message}`, "error");
		console.error("Search error:", error);
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
			const body = await response.text();
			let details = body;
			try {
				const parsed = JSON.parse(body);
				details = parsed.detail || parsed.message || JSON.stringify(parsed);
			} catch (parseError) {}
			throw new Error(details || `Unable to save notification (${response.status})`);
		}
		const result = await parseJsonResponse(response);
		setStatus("Notification saved successfully.");
		loadHistory();
		approveButton.textContent = "Already notified — no action needed";
		approveButton.disabled = true;
	} catch (error) {
		setStatus(`Save failed: ${error.message}`, "error");
		approveButton.disabled = false;
		approveButton.textContent = "Approve & Save Notification";
		console.error("Approve error:", error);
	}
}

form.addEventListener("submit", runSearch);
approveButton.addEventListener("click", approveNotification);
toggleDetailsButton.addEventListener("click", toggleResultDetails);
loadHistory();