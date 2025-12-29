import streamlit as st # type: ignore
import subprocess
import os
import time

# --- 1. إعدادات الصفحة وتصميمها (The Look & Feel) ---
st.set_page_config(
    page_title="AGL Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص CSS لجعله يشبه ChatGPT
st.markdown("""
<style>
    /* خلفية داكنة وأنيقة */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    /* تحسين شكل الرسائل */
    .stChatMessage {
        background-color: #262730;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    /* رسالة المستخدم بلون مختلف */
    .stChatMessage[data-testid="user-message"] {
        background-color: #2b313e;
    }
    /* إخفاء العناصر الزائدة */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. القائمة الجانبية (Control Center) ---
with st.sidebar:
    st.title("🧬 AGL Core")
    st.caption("Advanced General Intelligence System")
    
    st.markdown("---")
    
    # حالة النظام (محاكاة لاتصال السيرفر)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Memory", "Active", "49 Nodes")
    with col2:
        st.metric("Engines", "Ready", "47")
        
    st.markdown("---")
    st.info("💡 **تلميح:** النظام متصل بذاكرة طبية وقادر على التفكير المنطقي.")
    
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 3. المحادثة الرئيسية (Chat Interface) ---

# عنوان ترحيبي يختفي بعد أول رسالة
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>مرحباً بك في عقلك الرقمي الثاني</h1>
        <p style='color: #888;'>أنا جاهز للتحليل، التخطيط، وحل المعضلات المعقدة.</p>
    </div>
    """, unsafe_allow_html=True)

# عرض التاريخ
for message in st.session_state.messages:
    # streamlit's chat API expects role values 'user'/'assistant'
    try:
        with st.chat_message(message["role"], avatar=("👤" if message["role"] == "user" else "🧬")):
            st.markdown(message["content"]) 
    except Exception:
        st.markdown(message["content"])

# --- 4. المحرك (The Engine Connection) ---
if prompt := st.chat_input("اكتب سؤالك المعقد هنا..."):
    # عرض سؤال المستخدم
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # استدعاء النظام (Backend)
    with st.chat_message("assistant", avatar="🧬"):
        message_placeholder = st.empty()
        full_response = ""
        
        # تأثير "التفكير"
        with st.status("جاري التفكير وتحليل البيانات...", expanded=True) as status:
            st.write("🔄 استدعاء المخطط (Planner)...")
            time.sleep(0.5) # مجرد تأثير بصري
            st.write("🔎 البحث في الذاكرة (RAG)...")
            
            # --- هنا يتم الاتصال الحقيقي بسيرفرك ---
            try:
                # إعداد البيئة والأمر
                repo_root = r"D:\AGL\repo-copy"
                venv_python = r"D:\AGL\.venv\Scripts\python.exe"
                
                # تجهيز البيئة (كما طلبت: أتمتة المتغيرات)
                env_vars = os.environ.copy()
                env_vars['PYTHONPATH'] = repo_root
                env_vars['AGL_FORCE_EXTERNAL'] = '1'
                env_vars['AGL_FAST_MODE'] = '0'
                env_vars['AGL_DEBUG_ENGINES'] = '0'
                env_vars['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'

                # تشغيل السكربت الفعلي
                cmd = [
                    venv_python, 
                    f"{repo_root}\\scripts\\agl_master_entry.py", 
                    "--plan", 
                    "-q", prompt
                ]
                
                process = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    cwd=repo_root,
                    env=env_vars
                )
                
                raw_output = process.stdout
                
                # استخراج الإجابة النهائية بذكاء
                final_response = "عذراً، حدث خطأ داخلي أو لم يتم توليد إجابة."
                if raw_output:
                    if "--- FINAL ANSWER ---" in raw_output:
                        final_response = raw_output.split("--- FINAL ANSWER ---")[-1].strip()
                    elif "--- FINAL ANSWER (FROM DB) ---" in raw_output:
                        final_response = raw_output.split("--- FINAL ANSWER (FROM DB) ---")[-1].strip()
                    else:
                        # حاول استخراج مفيد من JSON-like أو improved_answer
                        final_response = raw_output.strip()

                status.update(label="تم الانتهاء!", state="complete", expanded=False)
                
            except Exception as e:
                final_response = f"⚠️ حدث خطأ في الاتصال بالنظام: {str(e)}"
                status.update(label="خطأ", state="error")

        # عرض الإجابة
        try:
            # بسيطة: نعرض الناتج كما هو
            message_placeholder.markdown(final_response)
        except Exception:
            message_placeholder.text(final_response)
        
    # حفظ الإجابة في التاريخ
    st.session_state.messages.append({"role": "assistant", "content": final_response})

# --- Footer with run instructions ---
st.markdown("---")
st.caption("لتشغيل الواجهة: `& 'D:\\AGL\\.venv\\Scripts\\python.exe' -m streamlit run D:\\AGL\\repo-copy\\app_ui.py`")
