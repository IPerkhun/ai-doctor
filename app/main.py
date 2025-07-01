from fastapi import FastAPI
from pydantic import BaseModel
from .state_manager import reset_user_state, graph


app = FastAPI()


class MessageInput(BaseModel):
    user_id: int
    message: str


@app.get("/")
def root():
    return {"message": "AI Doctor API запущен"}


@app.post("/message")
async def handle_message(input_data: MessageInput):
    # Загружаем текущее состояние или создаём новое
    thread_id = str(input_data.user_id)
    config = {"configurable": {"thread_id": thread_id}}

    # Запускаем граф с новым сообщением
    result = graph.invoke({"message": input_data.message}, config)

    if "q1" in result and "a1" not in result:
        return {"reply": result["q1"]}
    elif "q2" in result and "a2" not in result:
        return {"reply": result["q2"]}
    elif "final_recommendation" in result:
        return {"reply": result["final_recommendation"]}
    else:
        return {"reply": "Я пока не знаю, что ответить"}


@app.post("/reset")
async def reset_session(input_data: MessageInput):
    reset_user_state(str(input_data.user_id))
    return {"reply": "Сессия сброшена"}
