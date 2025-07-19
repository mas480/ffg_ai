import logging
import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI  # новый импорт

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# === ЗАГРУЗКА КЛЮЧА ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("❌ OPENAI_API_KEY не найден в .env")
    exit(1)

client = OpenAI(api_key=api_key)  # ← новый клиент

SCORING_PROMPT_TEMPLATE = """
Ты — эксперт по качеству генераций LLM в сфере онлайн-знакомств и общения.

Проанализируй следующий ответ ИИ, выданный пользователю.

Оцени его по шкале от 1 до 5 по следующим критериям:

1. **Полезность** — насколько советы или анализ реально помогают пользователю.
2. **Персонализация** — адаптирован ли ответ под конкретный текст или изображение.
3. **Тон** — дружелюбный, поддерживающий, без формальностей и шаблонов.
4. **Конкретика** — есть ли примеры, чёткие рекомендации, а не общие фразы.
5. **Полнота** — охватывает ли ответ все ключевые аспекты задачи.

Верни JSON следующего вида:

{{
  "scores": {{
    "usefulness": int (1-5),
    "personalization": int (1-5),
    "tone": int (1-5),
    "specificity": int (1-5),
    "completeness": int (1-5)
  }},
  "comment": "Краткий разбор ответа: что хорошо, что можно улучшить"
}}

ТЕКСТ ДЛЯ ОЦЕНКИ:
----------------
{input_text}
----------------
"""

def score_response_with_gpt(input_text: str) -> dict:
    prompt = SCORING_PROMPT_TEMPLATE.format(input_text=input_text)
    logger.info("⚙️ Отправка текста на оценку через GPT-4o...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        logger.info("✅ Оценка получена.")

        json_text = re.search(r"\{.*\}", content, re.DOTALL).group(0)
        return json.loads(json_text)

    except Exception as e:
        logger.error(f"❌ Ошибка при оценке: {e}")
        return {"scores": {}, "comment": "Ошибка при попытке оценки."}


# === ТЕСТ ===
if __name__ == "__main__":
    test_text = """
    - Плюсы: Отличный свет, живая улыбка, образ приятный. Фото вызывает доверие и тёплое ощущение.
    - Минусы: Лёгкая тень на лице — стоит поправить при следующем фото.
    - Рекомендации: Добавить кадр с хобби или на открытом воздухе.
    - Итог: Фото годное! Оставляй.
    """
    result = score_response_with_gpt(test_text)

    print("🎯 ОЦЕНКИ:")
    for k, v in result.get("scores", {}).items():
        print(f"{k}: {v}/5")

    print("\n📝 КОММЕНТАРИЙ:")
    print(result.get("comment"))