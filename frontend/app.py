import streamlit as st
import requests
from api import churn_predict, health_check, xray_health_predict

st.set_page_config(
    page_title="AI Portfolio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_URL = "http://localhost:8000"
churn_api_endpoint = "/api/v1/churn_predict"
xray_api_endpoint = "/api/v1/xray_predict"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

.stApp { background: #0a0e1a; color: #e2e8f0; }

/* Hide Streamlit's own top bar & deploy button */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }

/* Push main content down so it doesn't hide under fixed nav */
.main .block-container {
    padding-top: 80px !important;
}

.top-nav {
    background: linear-gradient(135deg, #0f1629 0%, #1a1f3a 100%);
    border-bottom: 1px solid #2d3561;
    padding: 14px 32px;
    display: flex; align-items: center; justify-content: space-between;
    /* Fixed positioning */
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    border-radius: 0;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
.nav-brand { font-size: 1.3rem; font-weight: 700; color: #7c83fd; letter-spacing: -0.5px; }
.nav-icons { display: flex; gap: 20px; align-items: center; }
.nav-icon { font-size: 1.2rem; cursor: pointer; opacity: 0.7; transition: opacity 0.2s; }
.nav-icon:hover { opacity: 1; }
.nav-badge {
    background: linear-gradient(135deg, #7c83fd, #a78bfa);
    color: white; padding: 4px 12px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px;
}

.hero-card {
    background: linear-gradient(135deg, #1a1f3a 0%, #0f1629 50%, #1a1f3a 100%);
    border: 1px solid #2d3561; border-radius: 20px;
    padding: 40px; margin-bottom: 28px; position: relative; overflow: hidden;
}
.hero-card::before {
    content: ''; position: absolute; top: -50%; right: -20%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(124,131,253,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title { font-size: 2.2rem; font-weight: 700; color: #fff; margin: 0 0 8px; line-height: 1.2; }
.hero-accent { color: #7c83fd; }
.hero-sub { color: #8892b0; font-size: 1rem; margin: 0 0 20px; }
.tag {
    display: inline-block; background: rgba(124,131,253,0.15);
    color: #7c83fd; border: 1px solid rgba(124,131,253,0.3);
    padding: 4px 12px; border-radius: 20px; font-size: 0.78rem;
    font-weight: 600; margin: 3px; letter-spacing: 0.3px;
}

.project-card {
    background: linear-gradient(135deg, #141828 0%, #1a1f3a 100%);
    border: 1px solid #2d3561; border-radius: 16px;
    padding: 28px; height: 100%; transition: all 0.3s ease;
    position: relative; overflow: hidden;
}
.project-card:hover { border-color: #7c83fd; transform: translateY(-2px); }
.project-card::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #7c83fd, #a78bfa); opacity: 0;
    transition: opacity 0.3s;
}
.project-card:hover::after { opacity: 1; }
.project-icon { font-size: 2.2rem; margin-bottom: 14px; display: block; }
.project-title { font-size: 1.05rem; font-weight: 700; color: #fff; margin: 0 0 10px; }
.project-desc { color: #8892b0; font-size: 0.88rem; line-height: 1.6; margin: 0 0 16px; }
.tech-tag {
    display: inline-block; background: rgba(167,139,250,0.1);
    color: #a78bfa; border: 1px solid rgba(167,139,250,0.25);
    padding: 2px 10px; border-radius: 12px; font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace; margin: 2px;
}
.status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #4ade80; display: inline-block;
    margin-right: 6px; box-shadow: 0 0 8px #4ade80;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
.api-section {
    background: #0f1629; border: 1px solid #2d3561; border-radius: 12px;
    padding: 16px 20px; margin: 16px 0; font-family: 'JetBrains Mono', monospace;
}
.api-method { color: #4ade80; font-weight: 600; font-size: 0.82rem; }
.api-path { color: #7c83fd; font-size: 0.82rem; margin-left: 8px; }
.section-header {
    font-size: 1.4rem; font-weight: 700; color: #fff; margin: 32px 0 20px;
    padding-bottom: 12px; border-bottom: 1px solid #2d3561;
}
.about-card {
    background: linear-gradient(135deg, #1a1f3a, #141828);
    border: 1px solid #2d3561; border-radius: 20px; padding: 36px;
}
.skill-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.sidebar-item {
    padding: 10px 14px; border-radius: 10px; cursor: pointer;
    transition: all 0.2s; display: flex; align-items: center; gap: 10px;
}
.response-box {
    background: #0a0e1a; border: 1px solid #2d3561; border-radius: 10px;
    padding: 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
    color: #4ade80; margin-top: 12px; min-height: 60px;
}
</style>
""", unsafe_allow_html=True)

# ── Top Nav ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div class="nav-brand">⚡ AI.Portfolio</div>
  <div class="nav-icons">
    <span class="nav-icon">🔔</span>
    <span class="nav-icon">⚙️</span>
    <span class="nav-icon">🌐</span>
    <span class="nav-badge">v2.0 LIVE</span>
    <span class="nav-icon">👤</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Control all four sides */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Remove extra margin from first element */
div[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: 1rem !important;
}

/* Optional: remove extra wrapper padding */
section.main > div {
    padding-top: 0rem;
    padding-left: 0rem;
    padding-right: 0rem;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────

PROJECTS = [
    ("👤", "About Me"),
    ("🔄", "Churn Classification"),
    ("🩻", "X-ray Classification"),
    ("📚", "RAG Q&A System"),
    ("🎨", "AI Studio"),
    ("🤖", "Research Agents")
]

with st.sidebar:
    st.markdown("<div style='text-align:center;padding:8px 0 20px'><span style='font-size:2rem'>🧠</span><div style='color:#7c83fd;font-weight:700;font-size:1.1rem;margin-top:6px'>AI Projects Hub</div><div style='color:#8892b0;font-size:0.78rem'>FastAPI Powered</div></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#2d3561;margin:0 0 16px'>", unsafe_allow_html=True)
    
    selected = st.radio(
        "Navigate",
        [f"{e}  {n}" for e, n in PROJECTS],
        label_visibility="collapsed"
    )
    page = selected.split("  ", 1)[1].strip()

    st.markdown("<hr style='border-color:#2d3561;margin:16px 0'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#0f1629;border:1px solid #2d3561;border-radius:10px;padding:12px;font-size:0.78rem;color:#8892b0'>
      <div style='color:#4ade80;font-weight:600;margin-bottom:6px'><span class='status-dot'></span>API Status</div>
      <div>🟢 FastAPI Server</div>
      <div style='margin-top:4px;color:#475569;font-family:monospace;font-size:0.7rem'>localhost:8000</div>
    </div>
    """, unsafe_allow_html=True)

# ── Helper: call FastAPI ──────────────────────────────────────────────────────
def call_api(endpoint, payload=None):
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=8)
        return r.json()
    except Exception as e:
        return {"error": str(e), "note": "Start FastAPI server to enable live results"}

# ── Pages ─────────────────────────────────────────────────────────────────────
if page == "Churn Classification":
    st.markdown("""
    <div class="hero-card">
      <div class="hero-title">🔄 Customer Churn <span class="hero-accent">Classification</span></div>
      <div class="hero-sub">Predict which customers are at risk of leaving using ML models trained on behavioral data. XGBoost-based churn prediction system on the Telco dataset, deployed via FastAPI for real-time customer risk scoring.</div>
      <span class="tag">🧮 NumPy</span><span class="tag">🐼 Pandas</span><span class="tag">📉 Matplotlib</span><span class="tag">📊 XGBoost</span><span class="tag">🐍 scikit-learn</span><span class="tag">🔗 FastAPI</span>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        gender = st.selectbox("Gender", ["Male", "Female"])
        senior_citizen = st.selectbox("Senior Citizen", ["Yes", "No"])
        partner = st.selectbox("Partner", ["Yes", "No"])
        dependents = st.selectbox("Dependents", ["Yes", "No"])
        tenure = st.number_input("Customer Tenure (Months)",min_value=0 ,max_value=72,step=1)

    with c2:
        phone_service = st.selectbox("Phone Service", ["Yes", "No"])
        multiple_lines = st.selectbox("Multiple Lines", ["Yes", "No", "No phone service"])
        internet_service = st.selectbox("Internet Service", ["DSL", "No", "Fiber optic"])
        online_security = st.selectbox("Online Security", ["Yes", "No"])
        online_backup = st.selectbox("Online Backup", ["Yes", "No"])

    with c3:
        device_protection = st.selectbox("Device Protection", ["Yes", "No"])
        tech_support = st.selectbox("Tech Support", ["Yes", "No"])
        streaing_tv = st.selectbox("Streaming TV", ["Yes", "No"])
        streaming_movies = st.selectbox("Streaming Movies", ["Yes", "No"])
        contract = st.selectbox("Contract Type", ["Month-to-month", "One year", "Two year"])


    with c4:
        paperless_billing = st.selectbox("Paperless Billing", ["Yes", "No"])
        payment_method = st.selectbox("Payment Method", ["Electronic check", "Mailed check","Bank transfer (automatic)", "Credit card (automatic)"])
        monthly_charges = st.number_input("Monthly Charges",min_value=15.0 ,max_value=120.0,step=0.1)
        total_charges = st.number_input("Total Charges",min_value=15.0 ,max_value=9000.0,step=0.1)
    
    if st.button("🔍 Predict Churn Risk", use_container_width=True):
        result = churn_predict(churn_api_endpoint, {"gender": gender,"SeniorCitizen": senior_citizen, 
                                             "Partner": partner, "Dependents": dependents, "tenure": tenure, 
                                             "PhoneService": phone_service, "MultipleLines": multiple_lines, 
                                             "InternetService": internet_service, "OnlineSecurity": online_security, 
                                             "OnlineBackup": online_backup, "DeviceProtection": device_protection, 
                                             "TechSupport": tech_support, "StreamingTV": streaing_tv, 
                                             "StreamingMovies": streaming_movies, "Contract": contract, 
                                             "PaperlessBilling": paperless_billing, "PaymentMethod": payment_method, 
                                             "MonthlyCharges": monthly_charges, "TotalCharges": total_charges})
        st.subheader("Prediction Result")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Churn", "No" if not result['churn'] else "Yes")
        with col2:
            st.metric("Probability", f"{result['probability']*100:.2f}%")
        with col3:
            st.metric("Risk Level", result['risk_level'])

elif page == "X-ray Classification":
    st.markdown("""
    <div class="hero-card">
      <div class="hero-title">🩻 X-Ray Image <span class="hero-accent">Classification</span></div>
      <div class="hero-sub">MobileNetV2-based X-ray classification system for pneumonia detection, deployed via FastAPI for real-time inference.</div>
      <span class="tag">🧠 Deep Learning</span><span class="tag">🧱 CNN</span><span class="tag">⚙️ TensorFlow</span><span class="tag">⚙️ TFLite</span><span class="tag">📓 Colab Notebook</span>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload Chest X-Ray Image", type=["jpg", "png", "jpeg"])
    
    if uploaded:
        st.image(uploaded, width=300, caption="Uploaded X-Ray")
        if st.button("🔬 Analyze the Image", use_container_width=True):
            result = xray_health_predict(xray_api_endpoint, uploaded)
            #st.markdown(f'<div class="response-box">{result}</div>', unsafe_allow_html=True)
            st.subheader("🩺 X-ray Classification Result")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Prediction", value=result["label"])
            with col2:
                st.metric(label="Confidence", value=f"{result['confidence']*100:.2f}%")
            st.divider()
            st.subheader("Class Probabilities")
            col3, col4 = st.columns(2)
            probs = result["probabilities"]
            with col3:
                st.metric(label="NORMAL", value=f"{probs['NORMAL']*100:.2f}%")
            with col4:
                st.metric(label="PNEUMONIA",value=f"{probs['PNEUMONIA']*100:.2f}%")

    else:
        st.info("📤 Upload an X-ray image to begin analysis")

elif page == "RAG Q&A System":
    st.markdown("""
    <div class="hero-card">
      <div class="hero-title">📚 RAG-Based <span class="hero-accent">Question Answering</span></div>
      <div class="hero-sub">Retrieval-Augmented Generation system — upload documents and get precise answers with citations</div>
      <span class="tag">🔍 Vector DB</span><span class="tag">🦜 LangChain</span><span class="tag">📎 Embeddings</span><span class="tag">💬 LLM</span>
    </div>
    """, unsafe_allow_html=True)

    doc = st.file_uploader("Upload Knowledge Document (PDF / TXT)", type=["pdf", "txt"])
    question = st.text_input("Ask a question about the document", placeholder="What are the key findings?")
    st.markdown('<div class="api-section"><span class="api-method">POST</span><span class="api-path">/rag/query</span></div>', unsafe_allow_html=True)
    
    if st.button("💡 Get Answer", use_container_width=True) and question:
        result = call_api("/rag/query", {"question": question, "document": doc.name if doc else "default_kb"})
        st.markdown(f'<div class="response-box">{result}</div>', unsafe_allow_html=True)

elif page == "AI Studio":
    st.markdown("""
    <div class="hero-card">
      <div class="hero-title">🎨 AI Studio <span class="hero-accent">Content Generation</span></div>
      <div class="hero-sub">Multi-modal AI content creation — generate text, images, code, and marketing copy from prompts</div>
      <span class="tag">✍️ GPT-4</span><span class="tag">🖼️ DALL-E</span><span class="tag">💻 Codegen</span><span class="tag">📢 Copywriting</span>
    </div>
    """, unsafe_allow_html=True)

    mode = st.selectbox("Content Type", ["📝 Blog Post", "📢 Ad Copy", "💻 Code Snippet", "📧 Email Campaign"])
    prompt = st.text_area("Describe what you want to generate", placeholder="Write a product launch blog post for an AI analytics tool...", height=100)
    tone = st.select_slider("Tone", ["Formal", "Neutral", "Casual", "Witty"])
    st.markdown('<div class="api-section"><span class="api-method">POST</span><span class="api-path">/studio/generate</span></div>', unsafe_allow_html=True)
    
    if st.button("✨ Generate Content", use_container_width=True) and prompt:
        result = call_api("/studio/generate", {"type": mode, "prompt": prompt, "tone": tone})
        st.markdown(f'<div class="response-box">{result}</div>', unsafe_allow_html=True)

elif page == "Research Agents":
    st.markdown("""
    <div class="hero-card">
      <div class="hero-title">🤖 Autonomous <span class="hero-accent">Research Agents</span></div>
      <div class="hero-sub">Multi-agent framework that autonomously searches, reads, synthesizes and summarizes research on any topic</div>
      <span class="tag">🕸️ Web Search</span><span class="tag">🧩 LangGraph</span><span class="tag">📑 Summarizer</span><span class="tag">🔗 Multi-Agent</span>
    </div>
    """, unsafe_allow_html=True)

    topic = st.text_input("Research Topic", placeholder="Latest advances in quantum computing 2024")
    c1, c2 = st.columns(2)
    with c1:
        depth = st.select_slider("Research Depth", ["Quick", "Standard", "Deep"])
    with c2:
        sources = st.multiselect("Sources", ["ArXiv", "News", "Wikipedia", "GitHub"], default=["ArXiv", "News"])
    
    st.markdown('<div class="api-section"><span class="api-method">POST</span><span class="api-path">/agents/research</span></div>', unsafe_allow_html=True)
    
    if st.button("🚀 Launch Research Agent", use_container_width=True) and topic:
        with st.spinner("🔍 Agents working autonomously..."):
            result = call_api("/agents/research", {"topic": topic, "depth": depth, "sources": sources})
        st.markdown(f'<div class="response-box">{result}</div>', unsafe_allow_html=True)

elif page == "About Me":
    st.markdown("""
    <div class="about-card">
      <div style="display:flex;align-items:center;gap:20px;margin-bottom:24px">
        <div style="font-size:4rem">👨‍💻</div>
        <div>
          <div style="font-size:1.8rem;font-weight:700;color:#fff">Raj Pal</div>
          <div style="font-size:1.2rem;font-weight:700;color:#fff">Aspiring AI/ML Engineer</div>
          <div style="color:#7c83fd;font-size:1rem;margin:4px 0">Focused on building end-to-end machine learning and AI systems — from data preprocessing, feature engineering, model training and evaluation to scalable deployment.</div>
          <div style="color:#8892b0;font-size:0.85rem">📍 Dubai, UAE &nbsp;|&nbsp; 🏢 Open to opportunities</div>
        </div>
      </div>
      <hr style="border-color:#2d3561;margin:0 0 20px">
      <div style="color:#8892b0;line-height:1.8;margin-bottom:20px">
        I have hands-on experience working with computer vision and language models, along with building APIs and interactive applications using FastAPI and Streamlit. My work centers on taking models beyond experimentation into usable, real-world systems.
      </div>
      <div style="margin-bottom:16px">
        <div style="color:#fff;font-weight:600;margin-bottom:8px">🛠️ Core Stack</div>
        <span class="tag">Python</span><span class="tag">Numpy</span><span class="tag">Pandas</span><span class="tag">Matplotlib</span><span class="tag">Seaborn</span><span class="tag">Scikit-learn</span><span class="tag">PyTorch</span><span class="tag">TensorFlow</span><span class="tag">FastAPI</span><span class="tag">LangChain</span><span class="tag">Docker</span><span class="tag">AWS</span>
      </div>
      <div>
        <div style="color:#fff;font-weight:600;margin-bottom:8px">📬 Connect</div>
        <a href="https://www.linkedin.com/in/raj-pal-5283171a8/" target="_blank" class="tag">🔗 LinkedIn</a>
        <a href="https://github.com/Raj762648" target="_blank" class="tag">🐙 GitHub</a>
        <span class="tag">✉️ rajpal.sdme@gmail.com</span>
        <span class="tag">📞 +971 582533414</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#475569;font-size:0.78rem;padding:16px;border-top:1px solid #2d3561;margin-top:20px">
  ⚡ AI Portfolio &nbsp;|&nbsp; 🔗 FastAPI Backend &nbsp;|&nbsp; 🐍 Built with Streamlit &nbsp;|&nbsp; © 2025
</div>
""", unsafe_allow_html=True)
