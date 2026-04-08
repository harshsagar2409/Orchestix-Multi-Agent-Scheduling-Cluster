🚀 Orchestix: Multi-Agent Scheduling Cluster

🌟 Overview
Orchestix is a high-fidelity Multi-Agent Control Center designed to eliminate AI scheduling hallucinations. Instead of relying on a single prompt, it utilizes a sequential cluster of specialized agents to validate intent, align temporal context (specifically for 2026), and persist data with 100% logic transparency.

✨ Key Features
· Sequential Multi-Agent Flow: Uses 4 specialized nodes (Analyzer, Task, Notes, Optimizer) for verified task processing.
· 2026 Temporal Alignment: Hard-coded temporal context to handle future scheduling accurately without hallucinations.
· Interactive Calendar Grid: Real-time synchronization between the AI cluster and a visual dashboard.
· Live Audit Logs: Complete transparency with streaming system logs for every AI decision.
· Modern UI: Lag-free glassmorphism interface built with Tailwind CSS.

🛠️ Technology Stack
· AI Engine: Google Gemini 2.0 Flash (via google-genai SDK)
· Backend: Python 3.12 with FastAPI
· Frontend: Vanilla JS, Tailwind CSS, Space Grotesk & Inter Fonts
· Cloud Infrastructure: Google Cloud Run & Cloud Build

🚀 Getting Started
Clone the repo:
git clone https://github.com/harshsagar2409/Orchestix-Multi-Agent-Scheduling-Cluster

Install dependencies:
pip install -r requirements.txt

Run locally:
python main.py

Deploy to Cloud Run:
gcloud run deploy orchestix --source . --set-env-vars GEMINI_API_KEY="YOUR_KEY"

📊 System Workflow
1. User Input → Natural language command received by the Hub.
2. Analyzer Agent → Extracts reasoning and intent logic.
3. Task & Notes Agents → Formulate validated titles and 2026 timestamps.
4. Optimizer Agent → Syncs data to the SQLite cluster node.
5. UI Update → Dashboard reflects the new event and live logs instantly.
