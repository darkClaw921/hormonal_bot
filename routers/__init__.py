"""Роутеры для организации обработчиков."""
from aiogram import Router

from handlers.cycle_input import router as cycle_input_router
from handlers.menu import router as menu_router
from handlers.partners import router as partners_router
from handlers.settings import router as settings_router
from handlers.start import router as start_router

# Создаем главный роутер
main_router = Router()

# Подключаем все роутеры
main_router.include_router(start_router)
main_router.include_router(menu_router)
main_router.include_router(partners_router)
main_router.include_router(cycle_input_router)
main_router.include_router(settings_router)
