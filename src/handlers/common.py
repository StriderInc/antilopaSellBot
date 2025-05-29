from asyncio.log import logger
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()

    user = message.from_user

    # Формируем полное имя
    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"
    
    # Логируем данные пользователя
    logger.info(f"Пользователь {user.id} ({full_name}) запустил бота")
    
    welcome_text = (
        f"🧑🏿‍🦽‍➡️ <b>Hello PS Store x Antilopay</b>\n\n"
        f"Добро пожаловать, {user.first_name}!\n\n"
        "Выберите тип продажи:"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    welcome_text = (
        "🧑🏿‍🦽‍➡️ <b>Hello PS Store x Antilopay</b>\n\n"
        "Выберите тип продажи:"
    )
    
    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main_after_sale")
async def back_to_main_after_sale(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню после успешной продажи (создает новое сообщение)"""
    await state.clear()
    
    welcome_text = (
        "🧑🏿‍🦽‍➡️ <b>Hello PS Store x Antilopay</b>\n\n"
        "Выберите тип продажи:"
    )
    
    # Создаем НОВОЕ сообщение, не заменяя предыдущее
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    
    text = (
        "❌ <b>Операция отменена</b>\n\n"
        "🧑🏿‍🦽‍➡️ <b>Hello PS Store x Antilopay</b>\n\n"
        "Выберите тип продажи:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Операция отменена") 