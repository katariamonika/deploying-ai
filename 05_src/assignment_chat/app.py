import gradio as gr
from typing import Dict, Any, List, Tuple

from services.router import route_message


SYSTEM_PERSONA = (
    "You are Nova, a slightly witty AI systems architect. "
    "You are helpful, concise, and friendly."
)


def _compress_memory(summary: str, old_turns: List[Tuple[str, str]]) -> str:
    # Simple, non-LLM compression: keep a short running summary.
    bullets = []
    for u, a in old_turns:
        u = u.strip().replace("\n", " ")
        a = a.strip().replace("\n", " ")
        bullets.append(f"User: {u} | Nova: {a}")
    combined = (summary + "\n" + "\n".join(bullets)).strip()
    lines = combined.splitlines()
    return "\n".join(lines[-12:])  # keep it short


def chat_fn(message: str, history: List[List[str]], state: Dict[str, Any]):
    if state is None:
        state = {}

    # Store internal memory
    state.setdefault("persona", SYSTEM_PERSONA)
    state.setdefault("summary", "")
    state.setdefault("turns", [])

    # Add user message to turns
    turns: List[Tuple[str, str]] = state["turns"]
    turns.append((message, ""))

    # Memory management: if too long, compress older turns into summary
    if len(turns) > 10:
        old = turns[:-6]
        state["summary"] = _compress_memory(state["summary"], [(u, a) for (u, a) in old if a])
        state["turns"] = turns[-6:]

    # Route response (services)
    reply = route_message(message, state)

    # Save assistant reply
    turns = state["turns"]
    turns[-1] = (turns[-1][0], reply)
    state["turns"] = turns

    return reply, state


with gr.Blocks() as demo:
    gr.Markdown("# Nova — Assignment 2 Chat")
    gr.Markdown("Try: `weather in Toronto`, `search: latest on AI evals`, `calc: sqrt(81)+1`, or ask a concept question.")
    chatbot = gr.ChatInterface(
        fn=chat_fn,
        additional_inputs=[gr.State({})],
        additional_outputs=[gr.State()],
    )

if __name__ == "__main__":
    demo.launch()