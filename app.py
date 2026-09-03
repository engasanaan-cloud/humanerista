import os
import base64
import asyncio
from datetime import datetime
import streamlit as st
import pandas as pd

from humanitarian_agent import (
    VALID_SECTORS,
    validate_input_query,
    run_humanitarian_agent,
    evaluate_draft_assessment,
    generate_markdown_from_payload,
    generate_docx_from_payload
)

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Humanerista - MEAL Agent", 
    page_icon="🌐", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

@st.cache_data
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            mime_type = "image/png" if image_path.endswith(".png") else "image/jpeg"
            return f"data:{mime_type};base64,{encoded}"
    return None

# ---------------------------------------------------------
# 2. ACF BRANDED CUSTOM CSS + RADAR ANIMATION
# ---------------------------------------------------------
acf_custom_css = """
<style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; height: 0rem !important; display:none !important; }
    .stApp { background-color: #FFFFFF !important; color: #1E1E1E !important; }
    h1 { color: #005FB6 !important; font-family: 'Arial', sans-serif; font-size: 1.8rem !important; margin-bottom: 0.1rem !important; margin-top: 0rem !important; }
    
    /* Force sidebar to stay anchored on screen and ignore collapsed states */
    [data-testid="stSidebar"] { 
        transform: none !important;
        margin-left: 0 !important;
        visibility: visible !important;
        min-width: 21rem !important;
        max-width: 21rem !important;
        background-color: #F8F9FA !important; 
        border-right: 3px solid #52AE32 !important; 
    }

    /* Completely remove ONLY the collapse buttons (Fixed to stop hiding the Generate button) */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }

    [data-testid="stSidebar"] > div:first-child { 
        padding-top: 0.8rem !important; 
        padding-bottom: 0.5rem !important; 
        padding-left: 1rem !important; 
        padding-right: 1rem !important; 
    }
    
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }

    /* Force all Sidebar Labels and Text to ACF Blue */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] * { 
        color: #005FB6 !important; 
    }

    /* Centered Header Profile Styles */
    .profile-name {
        color: #005FB6 !important;
        font-size: 1.15rem !important;
        font-weight: bold !important;
        line-height: 1.2 !important;
        margin: 0 !important;
        text-align: center !important;
    }
    .profile-title {
        color: #555555 !important;
        font-size: 0.78rem !important;
        margin-top: 2px !important;
        margin-bottom: 0 !important;
        text-align: center !important;
    }

    /* Fix Input Widget Dark Backgrounds & Keep Input Text Dark */
    .stTextInput input, 
    .stTextArea textarea, 
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CCCCCC !important;
        color: #1E1E1E !important;
    }

    /* Ensure text typed into the inputs remains dark */
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] input {
        color: #1E1E1E !important;
        -webkit-text-fill-color: #1E1E1E !important;
    }

    /* Multiselect Tags Styling: ACF Blue background with white text */
    span[data-baseweb="tag"] { 
        background-color: #005FB6 !important; 
        color: #FFFFFF !important; 
        border: none !important;
    }
    
    /* Ensure tag label text inside multiselect stays clean white */
    span[data-baseweb="tag"] span { 
        color: #FFFFFF !important; 
    }

    /* Style the close icon (x) inside the tags to match white */
    span[data-baseweb="tag"] svg {
        fill: #FFFFFF !important;
    }

    /* Expander styling */
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary { background-color: #F8F9FA !important; }
    [data-testid="stExpander"] summary p { color: #005FB6 !important; font-weight: bold !important; }
    [data-testid="stExpander"] summary svg { fill: #005FB6 !important; }

    /* Generate Button Styling */
    div.stButton > button:first-child { 
        background-color: #EE7203 !important; 
        color: #FFFFFF !important; 
        font-weight: bold !important; 
        border-radius: 6px !important; 
        padding: 0.45rem 0.8rem !important; 
        border: none !important;
    }
    
    div[data-testid="stAlert"] { color: #1E1E1E !important; }
    div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] p { color: #1E1E1E !important; }
    
    .radar-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1.5rem; margin-top: 0.5rem; }
    .radar { width: 70px; height: 70px; background-color: rgba(0, 95, 182, 0.05); border-radius: 50%; position: relative; border: 2px solid #005FB6; box-shadow: 0 0 15px rgba(0, 95, 182, 0.3); overflow: hidden; }
    .radar::before { content: ''; position: absolute; top: 50%; left: 50%; width: 50%; height: 2px; background-color: #52AE32; transform-origin: 0 50%; animation: scan 1.5s linear infinite; box-shadow: 0 0 10px rgba(82, 174, 50, 0.8); }
    @keyframes scan { 0% { transform: translateY(-50%) rotate(0deg); } 100% { transform: translateY(-50%) rotate(360deg); } }
    .loading-text { margin-top: 10px; font-weight: bold; color: #005FB6; font-size: 1rem; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 0.7; } 50% { opacity: 1; } 100% { opacity: 0.7; } }
    
    .console-text { font-family: 'Courier New', Courier, monospace; color: #555 !important; font-size: 0.85rem; }

    ::-moz-selection { background-color: #FFFFFF !important; color: #005FB6 !important; }
    ::selection { background-color: #FFFFFF !important; color: #005FB6 !important; }
</style>
"""
st.markdown(acf_custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. SIDEBAR & CONTROLLER
# ---------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
found_avatar_path = next((p for p in ["avatar.png", "avatar_hd.png", os.path.join(script_dir, "avatar.png"), os.path.join(script_dir, "avatar_hd.png")] if os.path.exists(p)), None)

avatar_html = ""
if found_avatar_path:
    base64_str = get_image_base64(found_avatar_path)
    if base64_str:
        avatar_html = f'<img src="{base64_str}" width="55" height="55" style="border-radius:50%; border:2px solid #005FB6; margin-bottom: 6px; object-fit: cover; display: block; margin-left: auto; margin-right: auto;"/>'

st.sidebar.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin-top: -25px;">
        {avatar_html}
        <p class="profile-name">Abdallah Sanaan</p>
        <p class="profile-title">Senior MEAL Management Portal</p>
    </div>
    <hr style="margin-top: 0.6rem; margin-bottom: 0.8rem; border: 0; border-top: 1px solid #DDDDDD;">
""", unsafe_allow_html=True)

st.sidebar.markdown("**🎯 Assessment Parameters**")
target_location = st.sidebar.text_input("Target Location / Scope", value="Bint Jbeil District, South Lebanon")
selected_sectors = st.sidebar.multiselect("Target Sectors", options=VALID_SECTORS, default=["WASH", "Food Security"])
additional_context = st.sidebar.text_area("Specific Focus / Constraints", placeholder="e.g., Focus on IDPs in collective shelters", height=50)

button_container = st.sidebar.empty()
run_button = button_container.button("🚀 Generate Assessment Report", use_container_width=True, key="btn_start")

# ---------------------------------------------------------
# 4. MAIN DASHBOARD & ACTOR-CRITIC LOOP (ASYNC WRAPPER)
# ---------------------------------------------------------
st.title("🌐 Humanitarian MEAL Situational Assessment Agent")
st.markdown("**Automated multi-sector situational analysis synthesized via live web intelligence and verified against institutional MEAL standards.**")

async def execute_agentic_workflow():
    is_valid, error_msg = await validate_input_query(location=target_location, sectors=selected_sectors, additional_context=additional_context)
    
    if not is_valid:
        st.warning(f"⚠️ **Security Guardrail Triggered:** {error_msg}")
        button_container.button("🚀 Generate Assessment Report", use_container_width=True, key="btn_reset_invalid")
        return
        
    constructed_query = f"Location: {target_location}. Sectors: {', '.join(selected_sectors)}. Context: {additional_context.strip()}"
    
    loading_placeholder = st.empty()
    loading_placeholder.markdown("""
        <div class="radar-container">
            <div class="radar"></div>
            <div class="loading-text">Agent & Expert collaborating on report...</div>
        </div>
    """, unsafe_allow_html=True)

    with st.status("🔍 Gathering and Validating Humanitarian Intelligence...", expanded=True) as status:
        try:
            MAX_ITERATIONS = 3
            current_feedback = None
            final_payload = None
            iteration_count = 0
            session_id = f"session_{datetime.now().strftime('%H%M%S')}"

            for iteration in range(1, MAX_ITERATIONS + 1):
                iteration_count = iteration
                
                with st.expander(f"📋 Step {iteration}: Live Field Analysis & Review Progress", expanded=True):
                    st.markdown(f"<p class='console-text'>[System Initializer] Setting up parameters for {', '.join(selected_sectors)} in {target_location}...</p>", unsafe_allow_html=True)
                    st.markdown("<p class='console-text'>[Lead Researcher] Scanning official UN and humanitarian databases...</p>", unsafe_allow_html=True)
                    
                    draft_payload = await run_humanitarian_agent(
                        query=constructed_query if iteration == 1 else "",
                        session_id=session_id,
                        user_id="streamlit_user",
                        expert_feedback=current_feedback
                    )
                    st.markdown("<p class='console-text'>[Lead Researcher] Draft assessment synthesized. Submitting to Quality Review...</p>", unsafe_allow_html=True)
                    
                    st.markdown("<p class='console-text'>[Senior MEAL Verifier] Verifying data integrity, source dates, and confidence logic...</p>", unsafe_allow_html=True)
                    eval_result = await evaluate_draft_assessment(draft_payload)
                    st.markdown(f"<p class='console-text'>[Senior MEAL Verifier Insights]: {eval_result.expert_reasoning}</p>", unsafe_allow_html=True)

                if eval_result.is_approved:
                    st.success("✅ **Quality Verification Passed:** Assessment meets all MEAL standards and data integrity checks.")
                    final_payload = draft_payload
                    break
                else:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.error(f"⚠️ **Revision Required by Senior Reviewer**\n\n*Quality Notes:* {eval_result.feedback}")
                    with col2:
                        st.info("🔄 *Refining dataset with targeted corrections...*")
                    
                    current_feedback = eval_result.feedback
                    
                    if iteration == MAX_ITERATIONS:
                        st.warning("Maximum verification cycles reached. Displaying current draft.")
                        final_payload = draft_payload

            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            markdown_output = generate_markdown_from_payload(final_payload)
            json_str = final_payload.model_dump_json(indent=2)
            docx_stream = generate_docx_from_payload(constructed_query, timestamp_str, final_payload)
            
            status.update(label=f"✅ Assessment complete! (Total Iterations: {iteration_count})", state="complete", expanded=False)
            loading_placeholder.empty() 
            
            tab_report, tab_sources, tab_json, tab_downloads = st.tabs([
                "📄 Executive Report", 
                "🔎 Source Citation Inspector", 
                "📊 JSON Output", 
                "💾 Export"
            ])
            
            with tab_report:
                st.markdown(f"### 🌐 HUMANITARIAN SITUATIONAL ASSESSMENT REPORT\n**Generated:** {timestamp_str} | **Quality Iterations:** {iteration_count}\n\n---")
                st.markdown(markdown_output)
            
            with tab_sources:
                st.markdown("### 🔎 Source Citation Inspector")
                st.markdown("Transparency is critical. Below are the specific sources and confidence scores the agent assigned to each metric.")
                
                source_data = [{"Indicator": row.indicator_name, "Value": row.value_status, "Source Cited": row.source_and_date, "Confidence": row.confidence_score} for row in final_payload.matrix_rows]
                df_sources = pd.DataFrame(source_data)
                
                def highlight_confidence(val):
                    if val == 'High': return 'background-color: #d4edda; color: #155724'
                    elif val == 'Medium': return 'background-color: #fff3cd; color: #856404'
                    else: return 'background-color: #f8d7da; color: #721c24'
                
                st.dataframe(df_sources.style.map(highlight_confidence, subset=['Confidence']), use_container_width=True)

            with tab_json:
                st.json(json_str)
                
            with tab_downloads:
                st.subheader("Download Assessment Assets")
                col1, col2 = st.columns(2)
                col1.download_button("📄 Download Word Document (.docx)", docx_stream.getvalue(), f"assessment_{file_timestamp}.docx", use_container_width=True)
                col2.download_button("📥 Download JSON Payload (.json)", json_str, f"assessment_{file_timestamp}.json", use_container_width=True)

        except Exception as e:
            status.update(label="❌ Execution Failed", state="error", expanded=True)
            st.error(f"Detailed Error: {str(e)}")
            loading_placeholder.empty()
        finally:
            button_container.button("🚀 Generate Assessment Report", use_container_width=True, key="btn_reset_complete")

if run_button:
    button_container.button("⏳ Generating... Please wait", use_container_width=True, disabled=True, key="btn_waiting")
    asyncio.run(execute_agentic_workflow())
else:
    st.info("👈 Set your location and sectors in the sidebar and click **Generate Assessment Report** to begin.")