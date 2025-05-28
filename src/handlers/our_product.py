from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import OurProductStates
from keyboards import (
    get_console_keyboard, 
    get_position_keyboard, 
    get_confirmation_keyboard, 
    get_cancel_keyboard,
    get_back_to_main_keyboard,
    get_cancel_and_back_keyboard,
    get_console_keyboard_with_back
)
from models import OurProductData, validate_amount
from services.google_sheets import GoogleSheetsService

router = Router()


@router.callback_query(F.data == "our_product")
async def start_our_product(callback: CallbackQuery, state: FSMContext):
    """Начало процесса продажи нашего товара"""
    await state.set_state(OurProductStates.waiting_game_name)
    
    text = (
        "🎮 <b>Продажа нашего товара</b>\n\n"
        "Введите название игры:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(OurProductStates.waiting_game_name)
async def process_game_name(message: Message, state: FSMContext):
    """Обработка названия игры"""
    await state.update_data(game_name=message.text)
    await state.set_state(OurProductStates.choosing_console)
    
    text = (
        "🧩 <b>Выбор позиции</b>\n\n"
        "Выберите консоль:"
    )
    
    await message.answer(
        text,
        reply_markup=get_console_keyboard_with_back(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("console_"), OurProductStates.choosing_console)
async def process_console_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора консоли"""
    console = callback.data.split("_")[1]
    await state.update_data(console=console)
    await state.set_state(OurProductStates.choosing_position)
    
    text = (
        f"🎮 <b>Консоль: {console}</b>\n\n"
        "Выберите позицию:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_position_keyboard(console),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_console", OurProductStates.choosing_position)
async def back_to_console(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору консоли"""
    await state.set_state(OurProductStates.choosing_console)
    
    text = (
        "🧩 <b>Выбор позиции</b>\n\n"
        "Выберите консоль:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_console_keyboard_with_back(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("position_"), OurProductStates.choosing_position)
async def process_position_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора позиции"""
    _, console, position = callback.data.split("_")
    await state.update_data(position=position)
    await state.set_state(OurProductStates.waiting_ps_login)
    
    text = (
        "👤 <b>Логин PS</b>\n\n"
        "Введите логин PlayStation:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_and_back_keyboard("back_to_position"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_position")
async def back_to_position(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору позиции"""
    data = await state.get_data()
    console = data.get('console')
    await state.set_state(OurProductStates.choosing_position)
    
    text = (
        f"🎮 <b>Консоль: {console}</b>\n\n"
        "Выберите позицию:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_position_keyboard(console),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(OurProductStates.waiting_ps_login)
async def process_ps_login(message: Message, state: FSMContext):
    """Обработка логина PS"""
    await state.update_data(ps_login=message.text)
    await state.set_state(OurProductStates.waiting_comment)
    
    text = (
        "💬 <b>Комментарий</b>\n\n"
        "Введите комментарий (лид, ссылка на диалог):"
    )
    
    await message.answer(
        text, 
        reply_markup=get_cancel_and_back_keyboard("back_to_ps_login"), 
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_ps_login")
async def back_to_ps_login(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу PS логина"""
    await state.set_state(OurProductStates.waiting_ps_login)
    
    text = (
        "👤 <b>Логин PS</b>\n\n"
        "Введите логин PlayStation:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_and_back_keyboard("back_to_position"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(OurProductStates.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработка комментария"""
    await state.update_data(comment=message.text)
    await state.set_state(OurProductStates.waiting_amount)
    
    text = (
        "💰 <b>Сумма</b>\n\n"
        "Введите сумму:"
    )
    
    await message.answer(
        text, 
        reply_markup=get_cancel_and_back_keyboard("back_to_comment"), 
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_comment")
async def back_to_comment(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу комментария"""
    await state.set_state(OurProductStates.waiting_comment)
    
    text = (
        "💬 <b>Комментарий</b>\n\n"
        "Введите комментарий (лид, ссылка на диалог):"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_and_back_keyboard("back_to_ps_login"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(OurProductStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    """Обработка суммы и показ подтверждения"""
    try:
        # Валидируем и преобразуем сумму
        amount = validate_amount(message.text)
        
        await state.update_data(amount=amount)
        await state.set_state(OurProductStates.confirmation)
        
        data = await state.get_data()
        
        confirmation_text = (
            "✅ <b>Проверьте данные:</b>\n"
            f"----------------------------------------\n"
            f"🎮 <b>Игра:</b> {data['game_name']}\n\n"
            f"🧩 <b>Консоль:</b> {data['console']}\n\n"
            f"📍 <b>Позиция:</b> {data['position']}\n\n"
            f"👤 <b>Логин PS:</b> {data['ps_login']}\n\n"
            f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
            f"💰 <b>Сумма:</b> {amount:.2f} ₽\n"
        )
        
        await message.answer(
            confirmation_text,
            reply_markup=get_confirmation_keyboard(),
            parse_mode="HTML"
        )
        
    except ValueError as e:
        error_text = (
            f"❌ <b>Ошибка:</b> {str(e)}\n\n"
            "💰 Введите корректную сумму (например: 1000 или 1500.50):"
        )
        await message.answer(
            error_text, 
            reply_markup=get_cancel_and_back_keyboard("back_to_comment"), 
            parse_mode="HTML"
        )


@router.callback_query(F.data == "back_to_amount")
async def back_to_amount(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу суммы"""
    await state.set_state(OurProductStates.waiting_amount)
    
    text = (
        "💰 <b>Сумма</b>\n\n"
        "Введите сумму:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_and_back_keyboard("back_to_comment"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "confirm", OurProductStates.confirmation)
async def confirm_our_product(callback: CallbackQuery, state: FSMContext):
    """Подтверждение продажи нашего товара"""
    data = await state.get_data()
    
    try:
        # Создаем объект данных
        product_data = OurProductData(
            game_name=data['game_name'],
            console=data['console'],
            position=data['position'],
            ps_login=data['ps_login'],
            comment=data['comment'],
            amount=data['amount'],  # Теперь это уже float
            user_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Интеграция с Google Sheets
        sheets_service = GoogleSheetsService()
        success = sheets_service.add_product_sale_record(
            game_name=product_data.game_name,
            console=product_data.console,
            position=product_data.position,
            ps_login=product_data.ps_login,
            comment=product_data.comment,
            amount=product_data.amount,
            timestamp=product_data.created_at
        )
        
        # Проверяем результат записи в таблицу
        if success:
            success_text = (
                "✅ <b>Заказ успешно создан!</b>\n\n"
                f"💰 <b>Сумма:</b> {product_data.amount:.2f} ₽\n"
                "Ссылка на оплату будет отправлена менеджеру.\n"
                "✅ Данные записаны в таблицу."
            )
        else:
            success_text = (
                "⚠️ <b>Заказ создан с предупреждением</b>\n\n"
                f"💰 <b>Сумма:</b> {product_data.amount:.2f} ₽\n"
                "Ссылка на оплату будет отправлена менеджеру.\n"
                "❌ Ошибка записи в таблицу - обратитесь к менеджеру."
            )
        
        await callback.message.edit_text(
            success_text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        await state.clear()
        
    except ValueError as e:
        error_text = f"❌ <b>Ошибка при создании заказа:</b> {str(e)}"
        await callback.message.edit_text(
            error_text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "edit", OurProductStates.confirmation)
async def edit_our_product(callback: CallbackQuery, state: FSMContext):
    """Редактирование данных продажи нашего товара"""
    await state.set_state(OurProductStates.waiting_amount)
    
    text = (
        "💰 <b>Редактирование данных</b>\n\n"
        "Введите сумму:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_and_back_keyboard("back_to_comment"),
        parse_mode="HTML"
    )
    await callback.answer()


# Добавляем обработчик возврата к названию игры
@router.callback_query(F.data == "back_to_game_name")
async def back_to_game_name(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу названия игры"""
    await state.set_state(OurProductStates.waiting_game_name)
    
    text = (
        "🎮 <b>Продажа нашего товара</b>\n\n"
        "Введите название игры:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer() 