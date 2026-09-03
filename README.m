# 🌐 Humanerista: Agentic MEAL Assessment System

Automating multi-sector humanitarian situational assessments using an **Actor-Critic Multi-Agent Architecture**.

## 🚀 Overview
Writing a multi-sector humanitarian situational assessment usually takes 3 to 5 days of manual data gathering across UN and INGO databases. **Humanerista** automates this down to 90 seconds while rigorously preventing LLM hallucinations.

This project utilizes Google's Gemini 2.5-Flash and the Agent Development Kit (ADK) to create an autonomous feedback loop between two AI agents.

## 🧠 The Actor-Critic Architecture
1. **The Guardrail:** A deterministic Pydantic pipeline intercepts user input and blocks out-of-domain queries (e.g., pop culture, sports) or prompt-injection attacks before they reach the internet.
2. **The Junior MEAL Agent (Actor):** Uses the `google_search` tool restricted *strictly* to verified domains (`reliefweb.int`, `humdata.org`, `acaps.org`, `who.int`). It maps data to LCRP and Global Cluster standards. If data is missing, it is hard-coded to flag `[DATA GAP]` rather than hallucinate.
3. **The Expat Director (Critic):** Evaluates the Junior Agent's JSON output for logical errors, unverified source numbers, and weak recommendations. If the draft is rejected, the critique is injected into the Junior's session memory, forcing a retry until the standards are met.

## 🛠️ Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/engasanaan-cloud/humanerista.git
cd humanerista