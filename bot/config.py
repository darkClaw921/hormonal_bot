"""Конфигурация бота."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Класс для хранения конфигурации приложения."""
    
    # Токен бота
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hormonal_bot.db")
    
    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Дополнительные настройки
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def validate(cls) -> None:
        """Проверяет наличие обязательных переменных окружения."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")


def setup_logging(log_level: str = None) -> None:
    """Настраивает логирование для приложения."""
    level = log_level or Config.LOG_LEVEL
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
