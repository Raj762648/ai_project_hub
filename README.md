# End-to-End AI Platform (Deployed on AWS EC2)

## 📌 Project Overview
This project is a **full end-to-end AI platform** that integrates multiple machine learning and AI capabilities into a single application. The system is deployed on an **AWS EC2 (t2.micro)** instance and exposes services through a scalable backend and interactive frontend.

The platform combines:
- Tabular ML (Customer Churn Classification)
- Computer Vision (Pneumonia X-ray Classification)
- Retrieval-Augmented Generation (RAG) for document QA
- Research Agent for automated paper discovery and summarization

---

## 🚀 Key Features

### 1. Customer Classification
- Predicts customer churn
- Uses pre-trained model from previous project
- Handles structured/tabular data
- Returns probability and classification label

---

### 2. X-ray Image Classification
- Detects pneumonia from chest X-ray images
- Fine-tuned MobileNetV2 model
- Supports image upload and real-time inference
- Optimized using TensorFlow Lite for efficient prediction

---

### 3. RAG-based Question Answering (Chat with PDF)
- Upload a PDF document and interact with it conversationally
- Uses:
  - OpenAI API for LLM responses
  - Pinecone for vector database storage
- Pipeline:
  - Document ingestion → chunking → embedding → vector storage
  - Query → similarity search → context injection → answer generation

---

### 4. Research Agent
- Accepts a topic as input
- Searches for relevant research papers
- Extracts and summarizes key insights
- Provides simplified explanations for better understanding

---

## 🏗️ System Architecture

```
User (Browser)
   ↓
Streamlit Frontend
   ↓
FastAPI Backend (API Layer)
   ↓
---------------------------------
| ML Models | RAG | Research Agent |
---------------------------------
   ↓
External Services:
- OpenAI API
- Pinecone Vector DB

Deployment Stack:
- AWS EC2 (t2.micro)
- Nginx (Reverse Proxy)
```

---

## ⚙️ Tech Stack

### Backend
- FastAPI
- Python

### Frontend
- Streamlit

### Machine Learning
- Scikit-learn (Customer Classification)
- TensorFlow / Keras (X-ray Model)
- TensorFlow Lite (Inference Optimization)

### LLM & RAG
- OpenAI API
- Pinecone (Vector Database)

### DevOps / Deployment
- AWS EC2 (t2.micro)
- Nginx (Reverse Proxy & Routing)
- GitHub Actions (CI/CD)

---

## 🔄 CI/CD Pipeline
Continuous Integration and Deployment implemented using **GitHub Actions**.

### Workflow Includes:
- Code push triggers pipeline
- Dependency installation
- Linting / basic checks
- Deployment to EC2 instance via SSH
- Automatic service restart

---

## 📁 Project Structure
```
.
├── frontend/
│   └── streamlit_app.py
├── backend/
│   ├── main.py (FastAPI entry point)
│   ├── routes/
│   ├── services/
│   └── models/
├── rag/
│   ├── ingestion.py
│   ├── retriever.py
│   └── qa_chain.py
├── research_agent/
│   ├── agent.py
│   └── utils.py
├── nginx/
│   └── nginx.conf
├── .github/
│   └── workflows/
│       └── deploy.yml
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run Locally

### 1. Clone Repository
```bash
git clone https://github.com/your-username/ai-platform.git
cd ai-platform
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Backend (FastAPI)
```bash
uvicorn backend.main:app --reload
```

### 5. Run Frontend (Streamlit)
```bash
streamlit run frontend/streamlit_app.py
```

---

## 🌐 Deployment Details

- Hosted on AWS EC2 (t2.micro)
- Nginx used as reverse proxy to route:
  - `/api` → FastAPI backend
  - `/` → Streamlit frontend
- Public access via EC2 public IP / domain

---

## 📊 Results & Performance

### Customer Classification
- Accuracy: [INSERT]
- F1 Score: [INSERT]

### X-ray Classification
- Phase 2 Accuracy: [INSERT]
- F1 Score: [INSERT]

### RAG System
- Retrieval Accuracy: [INSERT]
- Response Latency: [INSERT]

---

## 🔐 Environment Variables
Create a `.env` file:
```
OPENAI_API_KEY=[YOUR_KEY]
PINECONE_API_KEY=[YOUR_KEY]
PINECONE_ENV=[YOUR_ENV]
```

---

## 🔮 Future Improvements
- Add authentication (JWT-based)
- Kubernetes deployment for scalability
- Caching layer for faster RAG responses
- Monitoring with Prometheus + Grafana

---

## 👨‍💻 Author
- Name: [YOUR_NAME]
- GitHub: [YOUR_GITHUB]
- LinkedIn: [YOUR_LINKEDIN]

---

## 📜 License
This project is licensed under the MIT License.

