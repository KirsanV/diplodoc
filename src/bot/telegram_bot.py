import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from database.database import SessionLocal
from services.task_services import TaskService
from config.config import config
from database.models import Problem

logger = logging.getLogger(__name__)

CHOOSING_RATING, CHOOSING_TOPIC = range(2)


class TelegramBot:
    """Класс Telegram бота"""

    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("search", self.search))

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('problems', self.start_problem_selection)],
            states={
                CHOOSING_RATING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_rating)
                ],
                CHOOSING_TOPIC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_topic)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        self.application.add_handler(conv_handler)

        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_text = f"""
Привет, {user.first_name}! 👋

Я бот для поиска задач с Codeforces. Вот что я умею:

🔍 /search - Найти задачу по названию или номеру
📚 /problems - Подобрать задачи по сложности и теме
ℹ️ /help - Показать справку

Начните с команды /problems для подбора задач!
        """
        await update.message.reply_text(welcome_text)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 **Справка по командам:**

/search - Поиск задачи
Пример: `/search 123A` или `/search binary search`

/problems - Подбор задач по фильтрам
Бот предложит выбрать сложность и тему

💡 **Советы:**
- Задачи обновляются каждый час
- Можно искать по номеру (123A) или названию
- Подборка всегда содержит задачи из разных контестов
        """
        await update.message.reply_text(help_text)

    async def start_problem_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса подбора задач"""
        db = SessionLocal()
        try:
            ratings = TaskService.get_available_ratings(db)

            if not ratings:
                await update.message.reply_text("❌ В базе данных пока нет задач. Попробуйте позже.")
                return ConversationHandler.END

            keyboard = []
            row = []
            for rating in ratings[:10]:
                button = KeyboardButton(f"⭐ {rating}")
                row.append(button)
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)

            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

            await update.message.reply_text(
                "🎯 Выберите сложность задачи:",
                reply_markup=reply_markup
            )

            return CHOOSING_RATING

        finally:
            db.close()

    async def select_rating(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора сложности"""
        try:
            rating_text = update.message.text
            rating = int(rating_text.replace("⭐ ", "").strip())
            context.user_data['rating'] = rating

            db = SessionLocal()
            try:
                topics = TaskService.get_available_topics(db)

                if not topics:
                    await update.message.reply_text("❌ Нет доступных тем.")
                    return ConversationHandler.END

                keyboard = []
                row = []
                for topic in topics[:15]:
                    button = KeyboardButton(f"📚 {topic}")
                    row.append(button)
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)

                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

                await update.message.reply_text(
                    f"🎯 Выбрана сложность: {rating}\n\nТеперь выберите тему:",
                    reply_markup=reply_markup
                )

                return CHOOSING_TOPIC

            finally:
                db.close()

        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, выберите сложность из предложенных вариантов.")
            return CHOOSING_RATING

    async def select_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора темы и показ результатов"""
        topic_text = update.message.text
        topic = topic_text.replace("📚 ", "").strip()
        rating = context.user_data.get('rating')

        db = SessionLocal()
        try:
            problems = TaskService.get_problems_by_filters(db, rating, topic, limit=10)

            if not problems:
                await update.message.reply_text(
                    f"❌ Не найдено задач с сложностью {rating} и темой '{topic}'. "
                    f"Попробуйте другие параметры."
                )
                return ConversationHandler.END

            response = "🎯 **Подборка задач**\n\n"
            response += f"⭐ Сложность: {rating}\n"
            response += f"📚 Тема: {topic}\n"
            response += f"📊 Найдено задач: {len(problems)}\n\n"

            for i, problem in enumerate(problems, 1):
                response += f"{i}. **{problem.full_code}**: {problem.name}\n"
                response += f"   👥 Решений: {problem.solved_count}\n"
                response += f"   🔗 [Открыть задачу]({problem.codeforces_url})\n\n"

            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=None
            )

            return ConversationHandler.END

        finally:
            db.close()

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /search"""
        if not context.args:
            await update.message.reply_text(
                "🔍 Использование: /search <номер или название задачи>\n"
                "Пример: /search 123A\n"
                "Пример: /search binary search"
            )
            return

        search_query = " ".join(context.args)
        db = SessionLocal()

        try:
            problems = TaskService.search_problems(db, search_query)

            if not problems:
                await update.message.reply_text(f"❌ Задачи по запросу '{search_query}' не найдены.")
                return

            if len(problems) == 1:
                problem = problems[0]
                response = self._format_problem_details(problem)
            else:
                response = f"🔍 **Найдено задач: {len(problems)}**\n\n"
                for i, problem in enumerate(problems[:10], 1):
                    response += f"{i}. **{problem.full_code}**: {problem.name}\n"
                    response += f"   ⭐ Сложность: {problem.rating or 'N/A'}\n"
                    response += f"   👥 Решений: {problem.solved_count}\n"
                    response += f"   🔗 [Открыть]({problem.codeforces_url})\n\n"

                if len(problems) > 10:
                    response += f"ℹ️ Показано 10 из {len(problems)} задач"

            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

        finally:
            db.close()

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений (для быстрого поиска)"""
        text = update.message.text

        if any(char.isdigit() for char in text) and any(char.isalpha() for char in text):
            db = SessionLocal()
            try:
                problems = TaskService.search_problems(db, text)
                if problems:
                    if len(problems) == 1:
                        response = self._format_problem_details(problems[0])
                    else:
                        response = f"🔍 **Найдено задач по запросу '{text}':**\n\n"
                        for i, problem in enumerate(problems[:5], 1):
                            response += f"{i}. **{problem.full_code}**: {problem.name}\n"
                            response += f"   🔗 [Открыть]({problem.codeforces_url})\n"

                    await update.message.reply_text(
                        response,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    return

            finally:
                db.close()

        await update.message.reply_text(
            "🤔 Не понял ваш запрос. Используйте:\n"
            "/search - для поиска задач\n"
            "/problems - для подбора по фильтрам\n"
            "/help - для справки"
        )

    def _format_problem_details(self, problem: Problem) -> str:
        """Форматирование детальной информации о задаче"""
        response = f"🎯 **Задача {problem.full_code}**\n\n"
        response += f"**Название:** {problem.name}\n"
        response += f"**Сложность:** {problem.rating or 'N/A'}\n"
        response += f"**Количество решений:** {problem.solved_count}\n"

        if problem.topics:
            topics = ", ".join([topic.name for topic in problem.topics])
            response += f"**Темы:** {topics}\n"

        response += f"\n🔗 [Открыть на Codeforces]({problem.codeforces_url})"

        return response

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущей операции"""
        await update.message.reply_text(
            "❌ Операция отменена.",
            reply_markup=None
        )
        return ConversationHandler.END


def run_bot():
    """Запуск бота (синхронная версия)"""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.error("Please set TELEGRAM_BOT_TOKEN in .env file")
        return

    bot = TelegramBot(config.TELEGRAM_BOT_TOKEN)

    logger.info("Starting Telegram bot polling...")

    try:
        bot.application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot polling stopped by user")
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        raise
