from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict

TOKEN = "8062757827:AAHNm-8S-bmCjLyZ5TwPK7_QynbfxOdVQLo"
WEB_APP_URL = "http://127.0.0.1:5000"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Играть 🎮", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я шахматный бот. Жми кнопку и начинай игру:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Используй /start чтобы начать игру против шахматного движка Stockfish!"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, Conflict):
        print("⚠️  Другой экземпляр бота уже запущен. Завершите его!")
    else:
        print(f"⚠️  Ошибка: {context.error}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_error_handler(error_handler)
    
    print("🔄 Попытка запуска бота...")
    try:
        app.run_polling()
    except Conflict:
        print("❌ Ошибка: Уже запущен другой экземпляр бота!")
        print("💡 Закройте все другие терминалы и попробуйте снова")
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")

if __name__ == "__main__":
    main()