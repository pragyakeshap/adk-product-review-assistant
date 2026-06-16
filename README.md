# 🤖 ADK Product Requirement Review Assistant

A **multi-agent AI workflow** built with [Google Cloud ADK (Agent Development Kit)](https://cloud.google.com/products/agent-development-kit) and **Gemini** to automatically analyze product requirements and produce an executive-ready implementation recommendation.

---

## 🧠 What It Does

Given a product requirement, this assistant runs a structured multi-agent pipeline that produces:

- ✅ Structured requirement analysis
- 🏗️ Google Cloud architecture recommendation
- 🔐 Risk & governance review
- 🧪 Test plan & validation scenarios
- 📋 Final executive-ready recommendation

---

## 🔄 Agent Workflow

```
User Input (Product Requirement)
        │
        ▼
┌─────────────────────────┐
│   Requirement Analyzer  │  → Breaks down functional & non-functional requirements
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Architecture Advisor  │  → Recommends Google Cloud + ADK architecture
└────────────┬────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│         Parallel Review Team           │
│  ┌─────────────────────────────────┐   │
│  │   Risk & Governance Reviewer    │   │  ← Run in parallel
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │      Test Case Generator        │   │  ← Run in parallel
│  └─────────────────────────────────┘   │
└────────────┬───────────────────────────┘
             │
             ▼
┌─────────────────────────┐
│    Final Summary Agent  │  → Produces final recommendation
└─────────────────────────┘
```

Orchestrated using:
- `SequentialAgent` — for step-by-step pipeline execution
- `ParallelAgent` — for concurrent risk review + test planning

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | Google Cloud ADK |
| LLM | Gemini 2.5 Flash (Vertex AI) |
| Deployment (optional) | Cloud Run |
| Observability | Cloud Logging |
| Language | Python 3.13 |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Google Cloud project with Vertex AI enabled
- [ADK installed](https://cloud.google.com/products/agent-development-kit)

### Setup

```bash
# Clone the repo
git clone https://github.com/pragyakeshap/adk-product-review-assistant.git
cd adk-product-review-assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your Google Cloud project settings
```

### Run

```bash
adk run product_review_agent
```

Or via the ADK web UI:

```bash
adk web
```

---

## 📁 Project Structure

```
adk-product-review-assistant/
├── product_review_agent/
│   ├── agent.py        # All agents and workflow definition
│   └── __init__.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📄 License

This project is for demonstration purposes.

---

## 🙌 Built With

- [Google Cloud ADK](https://cloud.google.com/products/agent-development-kit)
- [Gemini on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/overview)
