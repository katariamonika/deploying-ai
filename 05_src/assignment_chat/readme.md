# Assignment 2 — Nova (Conversational AI System)

## Overview
Nova is a chat-based assistant with a slightly witty “AI systems architect” personality. The app is implemented with a Gradio chat interface and maintains short-term conversation memory throughout the session.

To keep the system robust in environments where OpenAI quota is unavailable, the semantic service supports an offline TF-IDF style retrieval mode by default.

## How to Run
From the repo root:

```bash
uv run python 05_src/assignment_chat/app.py