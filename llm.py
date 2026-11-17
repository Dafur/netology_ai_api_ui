import os
import time
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)
from openai.types.chat import ChatCompletionMessageParam
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YANDEX_GPT_API_KEY")
FOLDER_ID = os.getenv("YANDEX_GPT_FOLDER_ID")

BASE_URL = "https://llm.api.cloud.yandex.net/v1"
MODEL = f"gpt://{FOLDER_ID}/yandexgpt-lite"

MSG_ACCESS = "Не настроен доступ к сервису."
MSG_UNAVAILABLE = "Сервис временно недоступен. Попробуйте позже."
MSG_NETWORK = "Не удалось получить ответ. Попробуйте ещё раз."
MSG_EMPTY = "Пустой ответ модели. Попробуйте переформулировать вопрос."

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def build_prompt(dish: str, people: str, format: str) -> list[ChatCompletionMessageParam]:
    if format == "Список + шаги":
        task = (
            "Составь список продуктов и пошаговый рецепт приготовления.\n"
            "Формат ответа:\n"
            "1. Продукты (списком с количеством под нужное число порций)\n"
            "2. Шаги приготовления (нумерованным списком, 5 - 8 пунктов)"
        )
    else:
        task = (
            "Составь список продуктов для приготовления блюда.\n"
            "Формат ответа: список продуктов с количеством под нужное число порций."
        )

    return [
        {
            "role": "system",
            "content": (
                "Ты — кулинарный помощник. Отвечай на русском языке, "
                "кратко и структурированно, без вступлений и лишних слов."
            ),
        },
        {
            "role": "user",
            "content": f"Блюдо: {dish}\nКоличество порций: {people}\n\nЗадача: {task}",
        },
    ]

def _call_model(messages: list[ChatCompletionMessageParam]) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=1000,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("empty response")
    return content

def _call_with_retry(messages: list[ChatCompletionMessageParam]) -> str:
    for attempt in range(2):  # 1 попытка + 1 повтор
        try:
            return _call_model(messages)
        except APIStatusError as e:
            status = e.status_code
            if 400 <= status < 500:
                # Доступ/настройка: повтор бессмысленен
                return MSG_ACCESS
            # 5xx — можно повторить
            if attempt == 0:
                time.sleep(1)
                continue
            return MSG_UNAVAILABLE
        except (APITimeoutError, APIConnectionError):
            if attempt == 0:
                time.sleep(1)
                continue
            return MSG_NETWORK
        except ValueError:
            # Пустой/битый ответ: повтор не поможет, тексту модели нужна правка
            raise
    return MSG_UNAVAILABLE

def generate_response(dish: str, people: str, format: str) -> str:

    if not dish.strip():
        return "Напишите, что хотите приготовить."
    if len(dish.strip()) > 100:
        return "Слишком длинный текст — сократите или разбейте на части."
    if not API_KEY or not FOLDER_ID:
        return MSG_ACCESS
    
    messages = build_prompt(dish, people, format)

    try:
        return _call_with_retry(messages)
    except ValueError:
        return MSG_EMPTY
    except APIStatusError:
        return MSG_ACCESS
    except (APITimeoutError, APIConnectionError):
        return MSG_NETWORK
    except Exception:
        return MSG_UNAVAILABLE
