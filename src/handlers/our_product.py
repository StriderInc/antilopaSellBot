from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import asyncio

from states import OurProductStates
from keyboards import (
    get_console_keyboard, 
    get_position_keyboard, 
    get_confirmation_keyboard, 
    get_cancel_keyboard,
    get_back_to_main_keyboard,
    get_cancel_and_back_keyboard,
    get_console_keyboard_with_back,
    get_main_menu_keyboard,
    get_payment_method_keyboard,
    get_final_confirmation_keyboard,
    get_back_to_main_after_sale_keyboard
)
from models import OurProductData, validate_amount
from services.google_sheets import GoogleSheetsService
from services.antilopay import AntilopayAPI
from services.payment_tracker import PaymentTracker
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "our_product")
async def start_our_product(callback: CallbackQuery, state: FSMContext):
    """Начало процесса продажи нашего товара"""
    await state.set_state(OurProductStates.waiting_game_name)
    
    text = (
        "🎮 <b>Название игры</b>\n\n"
        "Введите название игры:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    
    # Сохраняем message_id для последующего редактирования
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()


@router.message(OurProductStates.waiting_game_name)
async def process_game_name(message: Message, state: FSMContext):
    """Обработка названия игры"""
    await state.update_data(game_name=message.text)
    await state.set_state(OurProductStates.choosing_console)
    
    text = (
        "🧩 <b>Выбор консоли</b>\n\n"
        "Выберите консоль:"
    )
    
    # Удаляем сообщение пользователя и редактируем бота
    await message.delete()
    
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['bot_message_id'],
            reply_markup=get_console_keyboard_with_back(),
            parse_mode="HTML"
        )
    except:
        sent_message = await message.answer(
            text, 
            reply_markup=get_console_keyboard_with_back(), 
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=sent_message.message_id)


@router.callback_query(F.data.startswith("console_"), OurProductStates.choosing_console)
async def process_console_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора консоли"""
    console = callback.data.split("_")[1]
    await state.update_data(console=console)
    await state.set_state(OurProductStates.choosing_position)
    
    text = (
        f"🎮 <b>Выбор позиции</b>\n\n"
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
        "🧩 <b>Выбор консоли</b>\n\n"
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
        f"🎮 <b>Выбор позиции</b>\n\n"
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
    
    # Удаляем сообщение пользователя и редактируем бота
    await message.delete()
    
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['bot_message_id'],
            reply_markup=get_cancel_and_back_keyboard("back_to_ps_login"),
            parse_mode="HTML"
        )
    except:
        sent_message = await message.answer(
            text, 
            reply_markup=get_cancel_and_back_keyboard("back_to_ps_login"), 
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=sent_message.message_id)


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
            "━━━━━━━━━━━━━━━━\n"
            f"🎮 <b>Название игры:</b> {data['game_name']}\n\n"
            f"🧩 <b>Консоль:</b> {data['console']}\n\n"
            f"📍 <b>Позиция:</b> {data['position']}\n\n"
            f"👤 <b>Логин PS:</b> {data['ps_login']}\n\n"
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


@router.callback_query(F.data == "confirm", OurProductStates.confirmation)
async def confirm_our_product(callback: CallbackQuery, state: FSMContext):
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
    await state.set_state(OurProductStates.payment_method_selection)
    
    # Показываем выбор способа оплаты
    payment_text = (
        "✅ <b>Данные подтверждены!</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"🎮 <b>Название игры:</b> {data['game_name']}\n\n"
        f"🧩 <b>Консоль:</b> {data['console']}\n\n"
        f"📍 <b>Позиция:</b> {data['position']}\n\n"
        f"👤 <b>Логин PS:</b> {data['ps_login']}\n\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"💰 <b>Сумма:</b> {amount:.2f} ₽\n"
        "━━━━━━━━━━━━━━━━\n"
        "💲 <b>Выберите способ оплаты:</b>"
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_method_keyboard(),
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


@router.callback_query(F.data.startswith("payment_"), OurProductStates.payment_method_selection)
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора способа оплаты и переход к финальному подтверждению"""
    data = await state.get_data()
    payment_method = callback.data.replace("payment_", "")
    
    # Сохраняем выбранный способ оплаты
    await state.update_data(payment_method=payment_method)
    await state.set_state(OurProductStates.final_confirmation)
    
    # Переводим код способа оплаты в читаемый вид
    payment_names = {
        "CARD_RU": "💳 Банковская карта",
        "SBER_PAY": "🟢 SberPay", 
        "SBP": "⚡ СБП"
    }
    payment_display = payment_names.get(payment_method, payment_method)
    
    # Показываем финальное подтверждение
    final_text = (
        "💲 <b>Способ оплаты подтвержден!</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"🎮 <b>Название игры:</b> {data['game_name']}\n\n"
        f"🧩 <b>Консоль:</b> {data['console']}\n\n"
        f"📍 <b>Позиция:</b> {data['position']}\n\n"
        f"👤 <b>Логин PS:</b> {data['ps_login']}\n\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"💰 <b>Сумма:</b> {data['amount']:.2f} ₽\n\n"
        f"💲 <b>Способ оплаты:</b> {payment_display}\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔗 <b>Получите ссылку на оплату</b>"
    )
    
    await callback.message.edit_text(
        final_text,
        reply_markup=get_final_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "get_payment_link", OurProductStates.final_confirmation)
async def get_payment_link(callback: CallbackQuery, state: FSMContext):
    """Создание платежа и получение ссылки на оплату"""
    data = await state.get_data()
    
    try:
        # Создаем объект данных
        product_data = OurProductData(
            game_name=data['game_name'],
            console=data['console'],
            position=data['position'],
            ps_login=data['ps_login'],
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
        
        # Создаем платеж
        payment_result = antilopay.create_payment(
            amount=product_data.amount,
            product_name=product_data.game_name,
            client_login=product_data.ps_login,
            description=description,
            prefer_methods=prefer_methods
        )
        
        if payment_result and payment_result.get("success"):
            payment_url = payment_result.get("payment_url")
            payment_id = payment_result.get("payment_id")
            order_id = payment_result.get("order_id")
            
            # Переводим код способа оплаты в читаемый вид для отображения
            payment_names = {
                "CARD_RU": "💳 Банковская карта",
                "SBER_PAY": "🟢 SberPay", 
                "SBP": "⚡ СБП"
            }
            payment_display = payment_names.get(data['payment_method'], data['payment_method'])
            
            success_text = (
                "✅ <b>Платеж успешно создан!</b>\n"
                "━━━━━━━━━━━━━━━━\n"
                f"🎮 <b>Название игры:</b> {data['game_name']}\n\n"
                f"🧩 <b>Консоль:</b> {data['console']}\n\n"
                f"📍 <b>Позиция:</b> {data['position']}\n\n"
                f"👤 <b>Логин PS:</b> {data['ps_login']}\n\n"
                f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
                f"💰 <b>Сумма:</b> {product_data.amount:.2f} ₽\n\n"
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
            
            # Запускаем асинхронное отслеживание платежа
            tracker = PaymentTracker(callback.bot)
            asyncio.create_task(
                tracker.track_payment(
                    order_id=order_id,
                    payment_id=payment_id,
                    sale_data=product_data,  # Передаем OurProductData
                    chat_id=callback.message.chat.id,
                    payment_display=payment_display,
                    user_telegram_login=callback.from_user.username
                )
            )
            
            logger.info(f"Создан платеж {payment_id} (Order: {order_id}) на сумму {product_data.amount} ₽ для товара {product_data.game_name}")
            
        else:
            # Ошибка создания платежа
            error_message = payment_result.get("error", "Неизвестная ошибка") if payment_result else "Нет ответа от API"
            
            error_text = (
                "❌ <b>Ошибка создания платежа</b>\n\n"
                f"💰 <b>Сумма:</b> {product_data.amount:.2f} ₽\n"
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
            
            logger.error(f"Ошибка создания платежа для товара: {error_message}")
        
        await state.clear()
        
    except Exception as e:
        # Критические ошибки
        try:
            await callback.message.delete()
        except:
            pass
        
        logger.error(f"Критическая ошибка создания платежа для товара: {e}")
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
        
        await state.clear()


@router.callback_query(F.data == "back_to_payment_method", OurProductStates.final_confirmation)
async def back_to_payment_method(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору способа оплаты"""
    data = await state.get_data()
    await state.set_state(OurProductStates.payment_method_selection)
    
    payment_text = (
        "✅ <b>Данные подтверждены!</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"🎮 <b>Название игры:</b> {data['game_name']}\n\n"
        f"🧩 <b>Консоль:</b> {data['console']}\n\n"
        f"📍 <b>Позиция:</b> {data['position']}\n\n"
        f"👤 <b>Логин PS:</b> {data['ps_login']}\n\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"💰 <b>Сумма:</b> {data['amount']:.2f} ₽\n"
        "━━━━━━━━━━━━━━━━\n"
        "💲 <b>Выберите способ оплаты:</b>"
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_method_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# Добавляем обработчик возврата к названию игры
@router.callback_query(F.data == "back_to_game_name")
async def back_to_game_name(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу названия игры"""
    await state.set_state(OurProductStates.waiting_game_name)
    
    text = (
        "🎮 <b>Название игры</b>\n\n"
        "Введите название игры:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню (создает новое сообщение)"""
    await state.clear()
    
    text = (
        "🧑🏿‍🦽‍➡️ <b>Hello PS Store x Antilopay</b>\n\n"
        "Выберите тип продажи:"
    )
    
    await callback.message.answer(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer() 