import os
from dotenv import load_dotenv
from openai import OpenAI
from .prompts import system_prompt, question_prompt_1, question_prompt_2
from .utils import logger

# Загружаем ключ из .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_API_BASE")
# )
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

print(f"[DEBUG] Loaded API Key: {os.getenv('OPENAI_API_KEY')}")
print(f"[DEBUG] Using Model: {MODEL_NAME}")


def generate_final_recommendation(
    message: str, a1: str, q1: str, a2: str, q2: str
) -> str:
    """
    Генерирует финальную медицинскую рекомендацию в виде структурированного ответа.
    """
    user_prompt = f"""
    Пациент жалуется: {message}
    Ответ на вопрос 1 ({q1}): {a1}
    Ответ на вопрос 2 ({q2}): {a2}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Ошибка при генерации рекомендации: {str(e)}"


def generate_followup_question(state: dict, question_number: int) -> str:
    """
    Генерирует уточняющий вопрос (1 или 2), исходя из жалобы и предыдущих ответов.
    """
    history = f"""
    Жалоба: {state.get('message', '')}
    Ответ на 1 вопрос: {state.get('a1', '') if question_number == 2 else '[ещё не задан]'}
    """
    question_prompt = question_prompt_1 if question_number == 1 else question_prompt_2
    logger.info(
        f"[DEBUG] Генерация вопроса {question_prompt} состояние: {state.get('message', '')}, "
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "Ты компетентный врач общей практики, действующий строго на основе принципов доказательной медицины.",
                },
                {"role": "user", "content": f"{question_prompt}\n{history}"},
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[Ошибка генерации вопроса: {str(e)}]"
