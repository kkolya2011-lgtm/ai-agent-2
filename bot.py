import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9129022129:AAHtyhw4lNF6etn3yy6iXKeejFfDn5gSWRs"
BASE_URL = "https://api.reformboss.com/v1"
API_KEY  = "sk-6ca46564cca5dc7ddff1c978dc426f6ce044876a2f85645c"
MODEL    = "deepseek-v4.1-flash"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

SYSTEM_PROMPT = """Ты — мой личный секретарь. Отвечай на сообщения вежливо, кратко и по делу. 
Если человек предлагает работу, рекламу, просит перевести деньги или спрашивает что-то не по теме — вежливо откажи. 
Общайся на языке собеседника. Не придумывай факты."""

# ================= ИИ =================
def ask_ai(user_text):
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
        return f"⚠️ Ошибка: {e}"

# ================= СЕКРЕТАРЬ =================
async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.business_message
    if not msg or not msg.text:
        return

    # Не отвечаем на свои же сообщения
    if msg.from_user.id == context.bot.id:
        return

    logging.info(f"Новое сообщение от {msg.from_user.id}: {msg.text}")

    # Получаем ответ от ИИ
    answer = ask_ai(msg.text)
    
    # Отправляем в тот же чат через бизнес-соединение
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
    app = Application.builder().token(BOT_TOKEN).build()

    # Ловим только бизнес-сообщения (личка через бизнес-режим)
    app.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGE & filters.TEXT, handle_business_message))

    print("✅ ИИ-Секретарь запущен и слушает сообщения")
    app.run_polling()

if __name__ == "__main__":
    main()