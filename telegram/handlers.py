from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()


class MessageInput(BaseModel):
    user_id: int
    message: str


@app.post("/message")
async def handle_message(input_data: MessageInput):
    # Пока просто эхо
    return {"reply": f"Ты написал: {input_data.message}"}
