from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Literal
from .agent import generate_final_recommendation, generate_followup_question
from .utils import logger


class GraphState(TypedDict, total=False):
    user_id: int
    message: str
    initial_message: str
    q1: str
    a1: str
    q2: str
    a2: str
    final_recommendation: str


# Глобальный memory и graph, НО с поддержкой thread_id
memory = MemorySaver()


def start_node(state: GraphState) -> GraphState:
    logger.info("[START]: %s", state.get("message"))

    if "initial_message" not in state and "message" in state:
        state["initial_message"] = state["message"]

    if "q1" in state and "a1" not in state:
        state["a1"] = state["message"]
    elif "q2" in state and "a2" not in state:
        state["a2"] = state["message"]

    state.pop("message", None)
    logger.info(f"[STATE DEBUG] Текущее состояние: {state}")
    return state


def need_more_info(state: GraphState) -> Literal["ask_q1", "ask_q2", "generate_final"]:
    if "q1" not in state:
        return "ask_q1"
    elif "a1" not in state:
        return "ask_q2"
    elif "a2" not in state:
        return "ask_q2"
    else:
        return "generate_final"


def ask_q1(state: GraphState) -> GraphState:
    q = generate_followup_question(state, question_number=1)
    state["q1"] = q
    logger.info(f"[Q1] Вопрос 1: {q}")
    return state


def ask_q2(state: GraphState) -> GraphState:
    q = generate_followup_question(state, question_number=2)
    state["q2"] = q
    logger.info(f"[Q2] Вопрос 2: {q}")
    return state


def generate_final(state: GraphState) -> GraphState:
    result = generate_final_recommendation(
        message=state.get("initial_message", ""),
        a1=state.get("a1", ""),
        q1=state.get("q1", ""),
        a2=state.get("a2", ""),
        q2=state.get("q2", ""),
    )
    logger.info(f"[FINAL RECOMMENDATION]\n{result}")
    state["final_recommendation"] = result
    return state


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("start", start_node)
    builder.add_node("ask_q1", ask_q1)
    builder.add_node("ask_q2", ask_q2)
    builder.add_node("generate_final", generate_final)

    builder.set_entry_point("start")

    builder.add_conditional_edges(
        "start",
        need_more_info,
        {"ask_q1": "ask_q1", "ask_q2": "ask_q2", "generate_final": "generate_final"},
    )

    builder.add_edge("ask_q1", END)
    builder.add_edge("ask_q2", END)
    builder.add_edge("generate_final", END)

    return builder.compile(checkpointer=memory)


# Один graph на всё приложение
graph = build_graph()


def reset_user_state(user_id: str):
    memory.delete_thread(user_id)
    logger.info(f"[RESET] Граф очищен для пользователя {user_id}")
