from graph import compliance_pipeline

# Provide the inputs your teammate's Agent 1 expects
initial_state = {
    "target_region": "India",
    "target_sector": "Heavy Industry"
}

print("--- Starting Pipeline Integration Test ---")
# This triggers the entire flow
final_state = compliance_pipeline.invoke(initial_state)

print(f"\nFinal State Keys: {list(final_state.keys())}")
print(f"CSO Found: {final_state.get('cso_contact_info')}")
print(f"Outreach Draft Generated: {bool(final_state.get('final_outreach_draft'))}")