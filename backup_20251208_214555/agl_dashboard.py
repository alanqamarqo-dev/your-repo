import streamlit as st # type: ignore
import json
import os
import glob
import pandas as pd # type: ignore
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="AGL Genesis Dashboard", page_icon="🧬", layout="wide")

# المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "workers", "..", "..", "artifacts") # تعديل المسار حسب هيكليتك
AUDIT_FILE = os.path.join(ARTIFACTS_DIR, "system_audit.json")
MODULES_DIR = os.path.join(BASE_DIR, "dynamic_modules")

def load_data():
    if os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# === الهيدر ===
st.title("🧬 AGL Genesis: Consciousness Monitor")
st.markdown("---")

data = load_data()

# === مؤشرات الحالة (KPIs) ===
col1, col2, col3, col4 = st.columns(4)

if data:
    state = data.get("cognitive_state", {})
    metrics = data.get("operational_metrics", {})
    
    col1.metric("Evolution Stage", state.get("evolution_stage", "Unknown"), "Active")
    col2.metric("Safety Status", metrics.get("safety_health", "Unknown"), "🛡️")
    col3.metric("Last Audit", data.get("timestamp", "").split("T")[1][:8])
else:
    col1.metric("Status", "Offline", "❌")

# === الأقسام الرئيسية ===
tab1, tab2 = st.tabs(["🛠️ Self-Written Modules", "🧠 Brain Activity"])

with tab1:
    st.subheader("Dynamic Capabilities (Self-Engineered)")
    if os.path.exists(MODULES_DIR):
        files = glob.glob(os.path.join(MODULES_DIR, "*.py"))
        modules = [os.path.basename(f) for f in files if "__init__" not in f]
        
        if modules:
            selected_module = st.selectbox("Select a module to inspect:", modules)
            if selected_module:
                with open(os.path.join(MODULES_DIR, selected_module), 'r', encoding='utf-8') as f:
                    code = f.read()
                st.code(code, language='python')
                st.success(f"Verified: {selected_module} is active and loaded.")
        else:
            st.info("No modules created yet. Waiting for Self-Engineer...")
    else:
        st.error("Dynamic Modules directory not found.")

with tab2:
    st.subheader("System Weights & Logic")
    if data:
        weights = data.get("cognitive_state", {}).get("current_iq_weights", {})
        st.json(weights)
        
        st.subheader("Latest Insights")
        insights = data.get("memory_integration", {}).get("last_night_insight", [])
        for insight in insights:
            st.info(f"💡 {insight}")

# === التحديث التلقائي ===
if st.button("Refresh Data"):
    st.experimental_rerun()
