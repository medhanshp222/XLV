

## Project Overview
XLV COMPLIANCE is an advanced, multi-agent system designed to revolutionize ESG (Environmental, Social, and Governance) compliance auditing. The platform automates the end-to-end process of researching regulatory mandates, extracting sustainability metrics from complex corporate reports, identifying compliance gaps, and generating data-backed strategic outreach.

By leveraging **LangGraph** for orchestration, **Gemini** for reasoning, and a custom **PDF Precision Loader** for high-accuracy RAG, AuditFlow AI transforms days of manual auditing into an autonomous, scalable pipeline.

---

## Business Value & Use Cases

In today’s regulatory landscape, organizations face an "ESG Data Paradox": they are collecting massive amounts of sustainability data but struggle to extract real-time insights against constantly shifting regional mandates. Manual auditing—hunting through 300-page PDFs and cross-referencing them against new government gazettes—is slow, expensive, and prone to human error.

**XLV COMPLIANCE** transforms this manual grind into an autonomous, scalable business advantage.

### Key Applications

* **Automated Enterprise Auditing:** Corporations can continuously monitor their internal metrics against the latest regional laws without waiting for a quarterly consultant review. The system definitively flags non-compliance (e.g., exceeding water-usage benchmarks in a specific region) in seconds.
* **Scaling ESG Consulting Firms:** Advisory firms can use this pipeline to automate their initial gap analysis. Instead of spending 40 hours reading a client's BRSR report, consultants can feed the parameters into the pipeline and immediately jump to high-level strategic planning.
* **Proactive B2B Outreach (Sales/Advisory):** By utilizing **Agent 4**, B2B service providers can automatically generate personalized, data-backed outreach to a Chief Sustainability Officer (CSO). The system identifies a specific regulatory failure and drafts an email offering a targeted solution, turning compliance gaps into immediate revenue opportunities.
---

## Team Details
*   **Team Name**: COMMIT_AND_CONQUER
*   **Team Members**:
    *   [P.MEDHANSH] - [Rollno-23071A67H0][Email-medhanshp222@gmail.com]
    *   [CH.BINDU] - [Rollno-23071A67E2][Email-binduchandanamnaidu@gmail.com]


---

## GitHub Repository
https://github.com/medhanshp222/XLV

---

## Setup Instructions

### Prerequisites
*   Python 3.11+
*   install uv (for environment and dependency management)
*   An active Google Gemini API Key

### Installation
1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/medhanshp222/XLV]
    cd XLV
    ```

2.  **Setup the environment**:
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv sync #to install all the packages and dependencies
    ```

3.  **Configure environment variables**:
    Create a `.env` file in the root directory and add your API keys:
    ```env
    GEMINI_API_KEY=your_key_here
    TAVILY_API_KEY=your_key_here
    ```

4.  **Running the System**:
    Start the backend and frontend server:
    ```bash
    uvicorn app:app --reload --host 127.0.0.1 --port 8000
    ```

5.  **Accessing the Application**:
    Once the server is running, open your web browser and navigate to:
    ```
    [http://127.0.0.1:8000](http://127.0.0.1:8000)
    ```

---

## Additional Notes
*   **Agentic Orchestration**: The pipeline utilizes LangGraph to maintain a shared state across four specialized agents, ensuring seamless data flow from regulatory research to strategy drafting.
*   **Scalability**: The architecture is modular; regulatory mandates and sustainability metrics can be updated by simply modifying the agentic plan, without requiring a full codebase refactor.

## Future Scope

While the current architecture successfully automates text-based compliance auditing, the next phase of development will focus on predictive intelligence and multi-modal data integration:

* **Predictive ESG Forecasting:** Moving beyond current-state analysis by implementing time series forecasting models. By analyzing historical sustainability metrics, the system will project a company's future carbon or water-usage trajectory, warning them of potential compliance breaches before they occur.
* **Multi-Modal Compliance Verification:** Expanding the data extraction engine to process more than just text. Future iterations will integrate computer vision models capable of analyzing satellite imagery or facility photographs to physically verify environmental claims—such as monitoring local land-use changes, deforestation, or physical waste management.
* **Direct Enterprise ERP Integration:** Bypassing the need for annual PDF reports entirely by building automated data extraction pipelines that plug directly into a company’s accounting and financial software, enabling real-time, continuous compliance monitoring.
* **Global Framework Expansion:** Scaling Agent 1's planner logic to support complex, cross-border regulatory frameworks such as the European Union’s CSRD (Corporate Sustainability Reporting Directive) and global ISSB standards.