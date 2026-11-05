import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9129022129:AAHtyhw4lNF6etn3yy6iXKeejFfDn5gSWRs"
API_KEY   = "kl_live_80z8OomiOjtDR7MQvExhJk6sYy4u4dTe"
MODEL     = "deepseek-v4-pro"  # Или "deepseek-flash", если хочешь скорость

# Список возможных путей. Бот сам найдет рабочий.
BASE_URLS = [
    "https://klinch.app/v1",
    "https://klinch.app/api/v1",
    "https://api.klinch.app/v1",
    "https://klinch.app"
]

client = None
working_url = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

SYSTEM_PROMPT = """Ты — мой личный секретарь. Отвечай на сообщения вежливо, кратко и по делу. 
Если человек предлагает работу, рекламу, просит перевести деньги или спрашивает что-то не по теме — вежливо откажи. 
Общайся на языке собеседника. Не придумывай факты."""

# ================= АВТОПОДБОР URL =================
def init_client():
    global client, working_url
    for url in BASE_URLS:
        try:
            test_client = OpenAI(base_url=url, api_key=API_KEY)
            # Пробуем сделать самый дешевый запрос
            test_client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1
            )
            client = test_client
            working_url = url
            logging.info(f"✅ Успешно подключились к API по адресу: {url}")
            return True
        except Exception as e:
            logging.warning(f"❌ Не сработал адрес {url}: {e}")
    return False

# ================= ИИ =================
def ask_ai(user_text):
    if not client:
        return "⚠️ Ошибка: API не инициализирован (неверный ключ или адрес)."
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.4,
            max_tokens=500,
        )
        msg = resp.choices[0].message
        content = getattr(msg, "content", None) or ""
        reasoning = getattr(msg, "reasoning_content", None) or ""
        return (content or reasoning).strip() or "⚠️ Пустой ответ."
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        return f"⚠️ Ошибка API: {e}"

# ================= СЕКРЕТАРЬ =================
async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.business_message
    if not msg or not msg.text:
        return

    if msg.from_user.id == context.bot.id:
        return

    logging.info(f"Новое сообщение от {msg.from_user.id}: {msg.text}")

    answer = ask_ai(msg.text)
    
    try:
        await context.bot.send_message(
            chat_id=msg.chat_id,
            text=answer[:4000],
            business_connection_id=msg.business_connection_id
        )
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

# ================= ЗАПУСК =================
def main():
    print("⏳ Проверяем подключение к API Klinch...")
    if not init_client():
        print("❌ Не удалось подключиться ни к одному из адресов. Проверь ключ и модель!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGE & filters.TEXT, handle_business_message))

    print("✅ ИИ-Секретарь запущен и слушает сообщения")
    app.run_polling()

if __name__ == "__main__":
    main()
