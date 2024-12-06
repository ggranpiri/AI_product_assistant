import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def log(update):
    """Логирует действия пользователя."""
    logger.info(f"User {update.effective_user.id} sent: {update.message.text if update.message else update.callback_query.data}")
