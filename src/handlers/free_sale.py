from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import FreeSaleStates
from keyboards import get_confirmation_keyboard, get_cancel_keyboard, get_back_to_main_keyboard, get_cancel_and_back_keyboard
from models import FreeSaleData, validate_amount
from services.google_sheets import GoogleSheetsService

router = Router()


@router.callback_query(F.data == "free_sale")
async def start_free_sale(callback: CallbackQuery, state: FSMContext):
    """Начало процесса свободной продажи"""
    await state.set_state(FreeSaleStates.waiting_service_name)
    
    text = (
        "📝 <b>Свободная продажа</b>\n\n"
        "Введите название услуги:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(FreeSaleStates.waiting_service_name)
async def process_service_name(message: Message, state: FSMContext):
    """Обработка названия услуги"""
    await state.update_data(service_name=message.text)
    await state.set_state(FreeSaleStates.waiting_client_login)
    
    text = (
        "👤 <b>Логин клиента</b>\n\n"
        "Введите логин клиента:"
    )
    
    await message.answer(
        text, 
        reply_markup=get_cancel_and_back_keyboard("back_to_service_name"), 
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_service_name")
async def back_to_service_name(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу названия услуги"""
    await state.set_state(FreeSaleStates.waiting_service_name)
    
    text = (
        "📝 <b>Свободная продажа</b>\n\n"
        "Введите название услуги:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(FreeSaleStates.waiting_client_login)
async def process_client_login(message: Message, state: FSMContext):
    """Обработка логина клиента"""
    await state.update_data(client_login=message.text)
    await state.set_state(FreeSaleStates.waiting_comment)
    
    text = (
        "💬 <b>Комментарий</b>\n\n"
        "Введите комментарий (лид, ссылка на диалог):"
    )
    
    await message.answer(
        text, 
        reply_markup=get_cancel_and_back_keyboard("back_to_client_login"), 
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_client_login")
async def back_to_client_login(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу логина клиента"""
    await state.set_state(FreeSaleStates.waiting_client_login)
    
    text = (
        "👤 <b>Логин клиента</b>\n\n"
        "Введите логин клиента:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_and_back_keyboard("back_to_service_name"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(FreeSaleStates.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработка комментария"""
    await state.update_data(comment=message.text)
    await state.set_state(FreeSaleStates.waiting_amount)
    
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
    await state.set_state(FreeSaleStates.waiting_comment)
    
    text = (
        "💬 <b>Комментарий</b>\n\n"
        "Введите комментарий (лид, ссылка на диалог):"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_and_back_keyboard("back_to_client_login"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(FreeSaleStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    """Обработка суммы и показ подтверждения"""
    try:
        # Валидируем и преобразуем сумму
        amount = validate_amount(message.text)
        
        await state.update_data(amount=amount)
        await state.set_state(FreeSaleStates.confirmation)
        
        data = await state.get_data()
        
        confirmation_text = (
            "✅ <b>Проверьте данные:</b>\n"
            f"----------------------------------------\n"
            f"📝 <b>Название:</b> {data['service_name']}\n\n"
            f"👤 <b>Логин:</b> {data['client_login']}\n\n"
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


@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    
    text = (
        "❌ <b>Операция отменена</b>\n\n"
        "🤖 <b>Hello Bot x Antilopay</b>\n\n"
        "Выберите тип продажи:"
    )
    
    from keyboards import get_main_menu_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Операция отменена")


@router.callback_query(F.data == "confirm", FreeSaleStates.confirmation)
async def confirm_free_sale(callback: CallbackQuery, state: FSMContext):
    """Подтверждение свободной продажи"""
    data = await state.get_data()
    
    try:
        # Создаем объект данных
        sale_data = FreeSaleData(
            service_name=data['service_name'],
            client_login=data['client_login'],
            comment=data['comment'],
            amount=data['amount'],  # Теперь это уже float
            user_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # TODO: Здесь будет интеграция с Antilopay API и Google Sheets
        
        sheets_service = GoogleSheetsService()
        success = sheets_service.add_free_sale_record(
            service_name=sale_data.service_name,
            client_login=sale_data.client_login,
            comment=sale_data.comment,
            amount=sale_data.amount,
            timestamp=sale_data.created_at
        )
        
        if success:
            success_text = (
                "✅ <b>Заказ успешно создан!</b>\n\n"
            f"💰 <b>Сумма:</b> {sale_data.amount:.2f} ₽\n"
                "Ссылка на оплату будет отправлена менеджеру.\n"
                "Данные записаны в таблицу."
            )
        else:
            success_text = (
                "⚠️ <b>Заказ создан с предупреждением</b>\n\n"
                f"💰 <b>Сумма:</b> {sale_data.amount:.2f} ₽\n"
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


@router.callback_query(F.data == "edit", FreeSaleStates.confirmation)
async def edit_free_sale(callback: CallbackQuery, state: FSMContext):
    """Редактирование данных свободной продажи"""
    await state.set_state(FreeSaleStates.waiting_amount)
    
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