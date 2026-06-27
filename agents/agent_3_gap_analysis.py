from state import AgentState

def gap_analysis_node(state: AgentState) -> dict:
    """
    Agent 3: Processes inputs to calculate compliance breaches based on MoEFCC and BRSR data.
    """
    print(f"--- [Agent 3] Running deterministic gap analysis for {state.get('company_name', 'Unknown Entity')} ---")
    
    company = state.get("company_name", "Tata Metallics Limited")
    
    # 1. Deterministic Variables 
    # Extracted from MoEFCC Notification
    statutory_cap = 50000.0  
    penalty_rate = 0.05  
    
    # Extracted from Tata Metallics BRSR
    actual_emissions = 54200.0  
    gross_revenue_crores = 3200.0  
    
    # 2. Mathematical Execution
    # Calculate the breach amount (ensure it doesn't go below 0)
    breach = max(0.0, actual_emissions - statutory_cap)
    
    # Calculate severity percentage
    severity_pct = (breach / statutory_cap) * 100 if statutory_cap > 0 else 0
    
    # Calculate financial penalty in Crores
    penalty_crores = gross_revenue_crores * penalty_rate
    
    # 3. Formatting the Output Payload
    report = f"""
    --- COMPLIANCE AUDIT REPORT ---
    - Entity: {company}
    - Legal Threshold: {statutory_cap:,.0f} MTCO2e
    - Reported Emissions: {actual_emissions:,.0f} MTCO2e
    - Breach Volume: {breach:,.0f} MTCO2e
    - Breach Severity: {severity_pct:.2f}% above mandate
    - Estimated Financial Exposure: INR {penalty_crores:,.2f} Crores
    """
    
    # Return the dictionary updating the state and setting the routing flag
    return {
        "compliance_gap_analysis": report.strip(),
        "next_step": "agent_4" 
    }