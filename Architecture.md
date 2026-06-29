# Agentic ESG Compliance Pipeline Architecture

## Overview
The Agentic ESG Compliance Pipeline is an autonomous, multi-agent system designed to transform the manual, error-prone process of ESG auditing into a scalable, data-backed business process. By leveraging **LangGraph** for orchestration and **Gemini** for reasoning, the pipeline eliminates manual PDF research and ensures high-precision extraction of regulatory and corporate data.

---

## High-Level Architecture Diagram

---

```text
=============================================================================
                      Vanilla JS & FastAPI Orchestrator
=============================================================================
                                     | (Initializes Context)
                                     v
+---------------------------------------------------------------------------+
|                   (( LANGGRAPH SHARED STATE / MEMORY ))                   |
|                                                                           |
|  [User Goals] | [Regulatory Baseline] | [ESG Metrics] | [Compliance Gaps] |
+---------------------------------------------------------------------------+
       ^                  ^                     ^                   ^
       | (Updates)        | (Updates)           | (Updates)         | (Updates)
       v                  v                     v                   v
+-------------+    +-------------+       +-------------+     +-------------+
|  AGENT 1:   |    |  AGENT 2:   |       |  AGENT 3:   |     |  AGENT 4:   |
|  Planner    |    |  Auditor    |       |  Analyst    |     |  Strategist |
+-------------+    +-------------+       +-------------+     +-------------+
       |                  |                     |                   |
 (Tool Access)      (Tool Access)         (Reasoning)         (Reasoning)
       |                  |
   [Tavily]       [FAISS Vector DB]
                  [PDF Precision Loader]

---

## Core Components

### 1. State Management
*   **LangGraph State Manager**: Serves as the "Shared State" for all agents. It ensures that data validated by one agent (e.g., regulatory rules from Agent 1) is immediately available to downstream agents (e.g., Agent 3), maintaining a single source of truth throughout the execution.

### 2. Multi-Agent Orchestration Pipeline
The system utilizes four specialized agents, each triggered by the LangGraph workflow:

#### **Agent 1: Market Initializer / Planner**
*   **Role**: Regulatory researcher.
*   **Tools**: Tavily Web Search API.
*   **Function**: Analyzes user inputs (Region/Sector) to search for real-time government mandates and instructions. It transforms unstructured web data into a structured **Compliance Baseline** stored in the Shared State.

#### **Agent 2: Corporate Scraper & ESG Auditor**
*   **Role**: Data extraction engine.
*   **Tools**: Tavily Web Search, FAISS/HuggingFace Vector DB, PDF Precision Loader.
*   **Function**: Downloads and parses corporate sustainability reports.
    *   **Retrieval-Augmented Generation (RAG)**: Uses semantic chunking and vector search to find relevant ESG metrics.
    *   **Precision Fallback (Page Buffer Harvest)**: If a metric is missing or low-confidence, the system avoids hallucination by triggering a "Precision Harvest." It retrieves the target page, plus the preceding and following pages $(p-1, p, p+1)$, ensuring complete context for complex tables.
    *   **Contact Extraction**: Identifies the Chief Sustainability Officer (CSO) contact details for outreach.

#### **Agent 3: Gap Analyst**
*   **Role**: Evaluator/Judge.
*   **Function**: Compares the "Ground Truth" regulatory baseline (from Agent 1) against the extracted corporate performance metrics (from Agent 2). It performs unit normalization and classifies the company status as **Compliant** or **Non-Compliant**.

#### **Agent 4: Report Finalizer / Strategist**
*   **Role**: Business communicator.
*   **Function**: Translates the gap analysis into high-value business output. It synthesizes findings into a professional, personalized outreach email addressed to the CSO, explaining compliance gaps and offering the platform as a remediation solution.

---

## Shared Agent Tool Stack
*   **Tavily Web Search**: Provides live access to up-to-date web intelligence.
*   **FAISS + HuggingFace**: Handles local, performant vector storage and semantic retrieval of high-volume PDF content.
*   **PDF Precision Loader**: The custom logic layer that executes the $(p-1, p, p+1)$ buffer harvest, specifically engineered to maintain table integrity across document page breaks.

---

## Execution Flow
1.  **Input**: User provides Region and Sector.
2.  **Orchestration**: FastAPI triggers the LangGraph workflow.
3.  **Research**: Agent 1 establishes the baseline.
4.  **Auditing**: Agent 2 populates the state with corporate performance data.
5.  **Analysis**: Agent 3 computes compliance status.
6.  **Outreach**: Agent 4 generates final deliverables (Report/Email).
7.  **Delivery**: Results are routed via REST API back to the Vanilla JS Frontend.