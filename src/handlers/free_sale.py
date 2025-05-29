from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import asyncio

from config import PAYMENT_METHOD_NAMES
from states import FreeSaleStates
from keyboards import (
    get_confirmation_keyboard, 
    get_cancel_keyboard, 
    get_back_to_main_keyboard, 
    get_cancel_and_back_keyboard, 
    get_back_to_main_after_sale_keyboard, 
)
from models import FreeSaleData, validate_amount
from services.antilopay import AntilopayAPI
from services.payment_tracker import PaymentTracker
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "free_sale")
async def start_free_sale(callback: CallbackQuery, state: FSMContext):
    """Начало процесса свободной продажи"""
    await state.set_state(FreeSaleStates.waiting_service_name)
    
    text = (
        "📝 <b>Название услуги</b>\n\n"
        "Введите название услуги:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    
    # Сохраняем message_id для последующего редактирования
    await state.update_data(bot_message_id=callback.message.message_id)
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
    
    # Удаляем сообщение пользователя и редактируем бота
    await message.delete()
    
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['bot_message_id'],
            reply_markup=get_cancel_and_back_keyboard("back_to_service_name"),
            parse_mode="HTML"
        )
    except:
        # Если не удалось отредактировать, отправляем новое
        sent_message = await message.answer(
            text, 
            reply_markup=get_cancel_and_back_keyboard("back_to_service_name"), 
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=sent_message.message_id)


@router.callback_query(F.data == "back_to_service_name")
async def back_to_service_name(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу названия услуги"""
    await state.set_state(FreeSaleStates.waiting_service_name)
    
    text = (
        "📝 <b>Название услуги</b>\n\n"
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
    
    # Удаляем сообщение пользователя и редактируем бота
    await message.delete()
    
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['bot_message_id'],
            reply_markup=get_cancel_and_back_keyboard("back_to_client_login"),
            parse_mode="HTML"
        )
    except:
        sent_message = await message.answer(
            text, 
            reply_markup=get_cancel_and_back_keyboard("back_to_client_login"), 
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=sent_message.message_id)


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
    
    # Удаляем сообщение пользователя и редактируем бота
    await message.delete()
    
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['bot_message_id'],
            reply_markup=get_cancel_and_back_keyboard("back_to_comment"),
            parse_mode="HTML"
        )
    except:
        sent_message = await message.answer(
            text, 
            reply_markup=get_cancel_and_back_keyboard("back_to_comment"), 
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=sent_message.message_id)


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
            "━━━━━━━━━━━━━━━━\n"
            f"📝 <b>Название услуги:</b> {data['service_name']}\n\n"
            f"👤 <b>Логин клиента:</b> {data['client_login']}\n\n"
            f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
            f"💰 <b>Сумма:</b> {amount:.2f} ₽\n"
        )
        
        # Удаляем сообщение пользователя и редактируем бота
        await message.delete()
        
        try:
            await message.bot.edit_message_text(
                text=confirmation_text,
                chat_id=message.chat.id,
                message_id=data['bot_message_id'],
                reply_markup=get_confirmation_keyboard(),
                parse_mode="HTML"
            )
        except:
            sent_message = await message.answer(
                confirmation_text,
                reply_markup=get_confirmation_keyboard(),
                parse_mode="HTML"
            )
            await state.update_data(bot_message_id=sent_message.message_id)
        
    except ValueError as e:
        error_text = (
            f"❌ <b>Ошибка:</b> {str(e)}\n\n"
            "💰 Введите корректную сумму (например: 1000 или 1500.50):"
        )
        
        # Удаляем сообщение пользователя и редактируем бота
        await message.delete()
        
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                text=error_text,
                chat_id=message.chat.id,
                message_id=data['bot_message_id'],
                reply_markup=get_cancel_and_back_keyboard("back_to_comment"),
                parse_mode="HTML"
            )
        except:
            sent_message = await message.answer(
                error_text, 
                reply_markup=get_cancel_and_back_keyboard("back_to_comment"), 
                parse_mode="HTML"
            )
            await state.update_data(bot_message_id=sent_message.message_id)


@router.callback_query(F.data == "confirm", FreeSaleStates.confirmation)
async def confirm_free_sale(callback: CallbackQuery, state: FSMContext):
    """Подтверждение данных и переход к выбору способа оплаты"""
    data = await state.get_data()
    
    try:
        amount = float(data['amount'])
    except (ValueError, KeyError):
        await callback.message.edit_text(
            "❌ Ошибка в данных. Начните заново.",
            reply_markup=get_back_to_main_keyboard()
        )
        await state.clear()
        return

    # Переходим к выбору способа оплаты
    await state.set_state(FreeSaleStates.payment_method_selection)
    
    # Показываем выбор способа оплаты в том же стиле
    payment_text = (
        "✅ <b>Данные подтверждены!</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Название услуги:</b> {data['service_name']}\n\n"
        f"👤 <b>Логин клиента:</b> {data['client_login']}\n\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"💰 <b>Сумма:</b> {amount:.2f} ₽\n"
        "━━━━━━━━━━━━━━━━\n"
        "💲 <b>Выберите способ оплаты:</b>"
    )
    
    from keyboards import get_payment_method_keyboard
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_method_keyboard(),
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


@router.callback_query(F.data.startswith("payment_"), FreeSaleStates.payment_method_selection)
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора способа оплаты и переход к финальному подтверждению"""
    data = await state.get_data()
    payment_method = callback.data.replace("payment_", "")
    
    # Сохраняем выбранный способ оплаты
    await state.update_data(payment_method=payment_method)
    await state.set_state(FreeSaleStates.final_confirmation)
    
    # Переводим код способа оплаты в читаемый вид
    payment_display = PAYMENT_METHOD_NAMES.get(payment_method, payment_method)
    
    # Показываем финальное подтверждение
    final_text = (
        "💲 <b>Способ оплаты подтвержден!</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Название услуги:</b> {data['service_name']}\n\n"
        f"👤 <b>Логин клиента:</b> {data['client_login']}\n\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"💰 <b>Сумма:</b> {data['amount']:.2f} ₽\n\n"
        f"💲 <b>Способ оплаты:</b> {payment_display}\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔗 <b>Получите ссылку на оплату</b>"
    )
    
    from keyboards import get_final_confirmation_keyboard
    await callback.message.edit_text(
        final_text,
        reply_markup=get_final_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "get_payment_link", FreeSaleStates.final_confirmation)
async def get_payment_link(callback: CallbackQuery, state: FSMContext):
    """Создание платежа и получение ссылки на оплату"""
    data = await state.get_data()
    
    try:
        # Создаем объект данных
        sale_data = FreeSaleData(
            service_name=data['service_name'],
            client_login=data['client_login'],
            comment=data['comment'],
            amount=data['amount'],
            user_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Показываем сообщение о создании платежа (заменяем текущее)
        await callback.message.edit_text(
            "⏳ <b>Создание платежа...</b>\n\nПожалуйста, подождите.",
            parse_mode="HTML"
        )
        await callback.answer()
        
        # Создаем платеж через Antilopay API
        antilopay = AntilopayAPI()
        
        # Определяем предпочтительный метод оплаты
        payment_method = data.get('payment_method')
        prefer_methods = [payment_method] if payment_method else None
        
        # Создаем описание платежа
        description = "Продажа товара"
        
        # Создаем платеж согласно ТЗ
        payment_result = antilopay.create_payment(
            amount=sale_data.amount,
            product_name=sale_data.service_name,
            client_login=sale_data.client_login,
            description=description,
            prefer_methods=prefer_methods
        )
        
        if payment_result and payment_result.get("success"):
            payment_url = payment_result.get("payment_url")
            payment_id = payment_result.get("payment_id")
            order_id = payment_result.get("order_id")
            
            # Переводим код способа оплаты в читаемый вид для отображения
            payment_display = PAYMENT_METHOD_NAMES.get(data['payment_method'], data['payment_method'])
            
            success_text = (
                "✅ <b>Платеж успешно создан!</b>\n"
                "━━━━━━━━━━━━━━━━\n"
                f"📝 <b>Название услуги:</b> {data['service_name']}\n\n"
                f"👤 <b>Логин клиента:</b> {data['client_login']}\n\n"
                f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
                f"💰 <b>Сумма:</b> {sale_data.amount:.2f} ₽\n\n"
                f"💲 <b>Способ оплаты:</b> {payment_display}\n\n"
                f"🆔 <b>Номер заказа:</b> <code>{order_id}</code>\n\n"
                f"🆔 <b>Идентификатор платежа:</b> <code>{payment_id}</code>\n"
                "━━━━━━━━━━━━━━━━\n"
                f"🔗 <b>Ссылка на оплату:</b>\n{payment_url}\n\n"
                "📤 Ссылка готова для отправки клиенту\n\n"
                "⏳ Оплату необходимо произвести в течение 10 минут"
            )
            
            # Удаляем сообщение "Создание платежа..." и создаем НОВОЕ сообщение об успехе
            try:
                await callback.message.delete()
            except:
                pass
            
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text=success_text,
                reply_markup=get_back_to_main_after_sale_keyboard(),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            # НОВОЕ: Запускаем асинхронное отслеживание платежа
            tracker = PaymentTracker(callback.bot)
            asyncio.create_task(
                tracker.track_payment(
                    order_id=order_id,
                    payment_id=payment_id,
                    sale_data=sale_data,
                    chat_id=callback.message.chat.id,
                    payment_display=payment_display,
                    user_telegram_login=callback.from_user.username
                )
            )
            
            logger.info(f"Создан платеж {payment_id} (Order: {order_id}) на сумму {sale_data.amount} ₽ для пользователя {sale_data.user_id}")
            
        else:
            # Ошибка создания платежа
            error_message = payment_result.get("error", "Неизвестная ошибка") if payment_result else "Нет ответа от API"
            
            error_text = (
                "❌ <b>Ошибка создания платежа</b>\n\n"
                f"💰 <b>Сумма:</b> {sale_data.amount:.2f} ₽\n"
                f"❗ <b>Ошибка:</b> {error_message}\n\n"
                "Обратитесь к администратору или попробуйте позже."
            )
            
            # Для ошибок тоже удаляем и создаем новое
            try:
                await callback.message.delete()
            except:
                pass
            
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text=error_text,
                reply_markup=get_back_to_main_after_sale_keyboard(),
                parse_mode="HTML"
            )
            
            # ДОБАВЛЕНО: Отправляем НОВОЕ сообщение с главным меню
            main_menu_text = (
                "🧑🏿‍🦽‍➡️ <b>Hello PS Store x Antilopay</b>\n\n"
                "Выберите тип продажи:"
            )
            
            await callback.message.answer(
                main_menu_text,
                reply_markup=get_back_to_main_keyboard(),
                parse_mode="HTML"
            )
            
            logger.error(f"Ошибка создания платежа: {error_message}")
        
        await state.clear()
        
    except Exception as e:
        # Аналогично для критических ошибок
        try:
            await callback.message.delete()
        except:
            pass
        
        logger.error(f"Критическая ошибка создания платежа: {e}")
        import traceback
        logger.error(f"Полная ошибка: {traceback.format_exc()}")
        
        error_text = (
            "❌ <b>Критическая ошибка</b>\n\n"
            f"💰 <b>Сумма:</b> {data.get('amount', 0):.2f} ₽\n"
            "❗ Произошла системная ошибка.\n\n"
            "Обратитесь к администратору."
        )
        
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=error_text,
            reply_markup=get_back_to_main_after_sale_keyboard(),
            parse_mode="HTML"
        )
        
        # ДОБАВЛЕНО: Отправляем НОВОЕ сообщение с главным меню
        main_menu_text = (
            "🧑🏿‍🦽‍➡️ <b>Hello PS Store x Antilopay</b>\n\n"
            "Выберите тип продажи:"
        )
        
        await callback.message.answer(
            main_menu_text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        
        await state.clear()


@router.callback_query(F.data == "back_to_payment_method", FreeSaleStates.final_confirmation)
async def back_to_payment_method(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору способа оплаты"""
    data = await state.get_data()
    await state.set_state(FreeSaleStates.payment_method_selection)
    
    payment_text = (
        "✅ <b>Данные подтверждены!</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Название услуги:</b> {data['service_name']}\n\n"
        f"👤 <b>Логин клиента:</b> {data['client_login']}\n\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"💰 <b>Сумма:</b> {data['amount']:.2f} ₽\n"
        "━━━━━━━━━━━━━━━━\n"
        "💲 <b>Выберите способ оплаты:</b>"
    )
    
    from keyboards import get_payment_method_keyboard
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_method_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()