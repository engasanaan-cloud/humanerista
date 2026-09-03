import asyncio
from datetime import datetime
from humanitarian_agent import (
    validate_input_query,
    run_humanitarian_agent,
    parse_markdown_to_pydantic,
    generate_docx_report
)

async def run_end_to_end_validation():
    print("\n==================================================")
    print(" 🚀 HUMANITARIAN PORTAL END-TO-END VALIDATION ")
    print("==================================================\n")

    # 1. Test Out-Of-Domain Guardrail Block
    test_invalid = "Provide a report on Shakira concert tour dates in Lebanon."
    print(f"1. Testing Invalid Input: '{test_invalid}'")
    is_valid, err_msg = validate_input_query(test_invalid)
    print(f"   [Result] Valid: {is_valid} | Guardrail Message: '{err_msg}'")
    assert is_valid is False, "❌ Guardrail Failed: Invalid query was accepted!"
    print("   ✅ Out-Of-Domain Guardrail Passed!\n")

    # 2. Test Valid MEAL Query Execution
    test_valid = "Provide a multi-sector assessment for Bint Jbeil District focusing on WASH, Food Security."
    print(f"2. Testing Valid Input: '{test_valid}'")
    is_valid, msg = validate_input_query(test_valid)
    assert is_valid is True, f"❌ Guardrail Failed on Valid Input: {msg}"
    print("   ✅ Input Guardrail Passed! Invoking Humanitarian Agent...\n")

    # 3. Execute Async Agent Call
    raw_output = await run_humanitarian_agent(test_valid)
    print("--- [AGENT RAW OUTPUT PREVIEW] ---")
    print(raw_output[:300] + "...\n-----------------------------------")

    # 4. Generate Word Document (.docx) & JSON Payload
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    docx_stream = generate_docx_report(test_valid, timestamp_str, raw_output)
    payload = parse_markdown_to_pydantic(test_valid, raw_output)

    # Save to disk
    with open(f"output_reports/validation_{file_timestamp}.docx", "wb") as f:
        f.write(docx_stream.getvalue())
        
    with open(f"output_reports/validation_{file_timestamp}.json", "w") as f:
        f.write(payload.model_dump_json(indent=2))

    print(f"✅ Word Document successfully generated: output_reports/validation_{file_timestamp}.docx")
    print(f"✅ JSON Payload successfully generated: output_reports/validation_{file_timestamp}.json")
    print("\n🎉 ALL SYSTEM VALIDATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_end_to_end_validation())