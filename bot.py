from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import requests
from gigachat import GigaChat
import os

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS") 
GIGACHAT_SCOPE = "GIGACHAT_API_PERS" 

TYPE, BUDGET, CLIMATE, DURATION, COMPANION = range(5)


def generate_with_gigachat(prompt: str) -> str:
    try:
        with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False, scope=GIGACHAT_SCOPE) as giga:
            response = giga.chat(prompt)
            return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка API GigaChat: {str(e)}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    menu_options = [["Активный", "Культурный"],
                    ["Религиозный", "Пляжный"],
                    ["Гастрономический", "Экотуризм"],
                    ["Выйти"]]
    reply_markup = ReplyKeyboardMarkup(menu_options, resize_keyboard=True)
    await update.message.reply_text(
        "Привет!🖐️ Я помогу выбрать идеальный город для путешествия.\n**Какой тип отдыха вас интересует?**\n\n"
        "Вы можете в любой момент нажать 'Выйти' или отправить /start для начала заново.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return TYPE


async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == "выйти":
        return await cancel(update, context)

    context.user_data["type"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(
        [["До 50 тыс. руб.", "50–100 тыс. руб."],
         ["100–200 тыс. руб.", "Не важно"],
         ["Выйти"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "**Какой у вас бюджет на поездку?💰**\n\n"
        "Вы можете в любой момент нажать 'Выйти' или отправить /start для начала заново.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return BUDGET


async def ask_climate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == "выйти":
        return await cancel(update, context)

    context.user_data["budget"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(
        [["Теплый", "Умеренный"],
         ["Холодный", "Любой"],
         ["Выйти"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "**Какой климат предпочитаете?⛅**\n\n"
        "Вы можете в любой момент нажать 'Выйти' или отправить /start для начала заново.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CLIMATE


async def ask_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == "выйти":
        return await cancel(update, context)

    context.user_data["climate"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(
        [["3–5 дней", "1–2 недели"],
         ["Месяц+", "Еще не решил"],
         ["Выйти"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "**На сколько планируете поездку?⌚**\n\n"
        "Вы можете в любой момент нажать 'Выйти' или отправить /start для начала заново.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return DURATION


async def ask_companion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == "выйти":
        return await cancel(update, context)

    context.user_data["duration"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(
        [["Один/с партнером", "С семьей"],
         ["С друзьями", "Групповой тур"],
         ["Выйти"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "**С кем вы путешествуете?🌎**\n\n"
        "Вы можете в любой момент нажать 'Выйти' или отправить /start для начала заново.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return COMPANION


async def generate_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == "выйти":
        return await cancel(update, context)

    context.user_data["companion"] = update.message.text

    prompt = f"""
    Пользователь ищет город для путешествия со следующими параметрами:
    - Тип отдыха: {context.user_data["type"]}
    - Бюджет: {context.user_data["budget"]}
    - Климат: {context.user_data["climate"]}
    - Длительность: {context.user_data["duration"]}
    - Компания: {context.user_data["companion"]}

    Дай 3 персонализированных варианта в формате:
    1. Город (Страна): 
       - 🌎Почему подходит: [1-2 предложения]
       - 💰Бюджет на поездку: [оценка]
       - 📍Совет: [что обязательно сделать]

    ВСЕГДА ОТПРАВЛЯЙ ЭМОДЗИ!!! ВСЕГДА делай красивое оформление выводимого сообщения. Например, используй смайлики, жирный шрифт, курсив...
    """

    processing_message = await update.message.reply_text("⌛️ Формирую ответ ...")

    gigachat_response = generate_with_gigachat(prompt)

    # Удаляем Markdown разметку, если есть проблемы с парсингом
    clean_response = gigachat_response.replace('*', '').replace('_', '').replace('`', '')

    await update.message.reply_text(
        f"Вот лучшие варианты для вас:\n\n{clean_response}\n\n"
        "Чтобы начать заново, отправьте /start",
        reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Диалог прерван. Чтобы начать заново, отправьте /start",
        reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
    )
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token("7811406174:AAEB3bjnw1cysP66ucHZ9-id1sRTrxLmssk").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_budget)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_climate)],
            CLIMATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_duration)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_companion)],
            COMPANION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_recommendation)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r'^Выйти$'), cancel)
        ]
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
