"""
Сервис для асинхронного отслеживания статуса платежей
"""

import asyncio
import logging
from typing import Dict, Any, Union
from aiogram import Bot

from services.antilopay import AntilopayAPI
from services.google_sheets import GoogleSheetsService
from models import FreeSaleData, OurProductData
from keyboards import get_back_to_main_after_sale_keyboard

logger = logging.getLogger(__name__)


class PaymentTracker:
    """Класс для отслеживания статуса платежей"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.antilopay = AntilopayAPI()
        self.sheets_service = GoogleSheetsService()
    
    async def track_payment(self, order_id: str, payment_id: str, 
                          sale_data: Union[FreeSaleData, OurProductData], chat_id: int, 
                          payment_display: str, user_telegram_login: str):
        """
        Асинхронное отслеживание платежа в течение 10 минут
        """
        logger.info(f"Начато отслеживание платежа {payment_id} (Order: {order_id})")
        
        # Проверяем статус каждые 30 секунд в течение 10 минут (20 попыток)
        max_attempts = 20
        check_interval = 30  # секунд
        
        for attempt in range(max_attempts):
            try:
                await asyncio.sleep(check_interval)
                
                # Проверяем статус платежа
                status_result = self.antilopay.check_payment_status(order_id)
                
                if not status_result.get("success"):
                    logger.warning(f"Ошибка проверки статуса платежа {payment_id}: {status_result.get('error')}")
                    continue
                
                status = status_result.get("status")

                logger.info(f"Статус платежа {payment_id}: {status} (попытка {attempt + 1}/{max_attempts})")
                
                if status == "SUCCESS":
                    # Платеж успешно оплачен
                    await self._handle_successful_payment(
                        order_id, payment_id, sale_data, chat_id, 
                        payment_display, status_result, user_telegram_login
                    )
                    return
                
                elif status in ["FAIL", "CANCEL", "EXPIRED"]:
                    # Платеж не удался
                    await self._handle_failed_payment(
                        order_id, payment_id, chat_id, status
                    )
                    return
                
                # Если статус PENDING - продолжаем ожидание
                
            except Exception as e:
                logger.error(f"Ошибка при проверке статуса платежа {payment_id}: {e}")
        
        # Время ожидания истекло
        await self._handle_timeout_payment(order_id, payment_id, chat_id)
    
    async def _handle_successful_payment(self, order_id: str, payment_id: str,
                                       sale_data: Union[FreeSaleData, OurProductData], chat_id: int,
                                       payment_display: str, status_result: Dict[str, Any], user_telegram_login: str):
        """Обработка успешного платежа"""
        try:
            amount_received = status_result.get("amount", sale_data.amount)
            # Определяем тип данных и записываем в соответствующую таблицу
            if isinstance(sale_data, FreeSaleData):
                sheets_success = self.sheets_service.add_free_sale_record(
                    service_name=sale_data.service_name,
                    client_login=sale_data.client_login,
                    comment=sale_data.comment,
                    amount=amount_received,
                    timestamp=sale_data.created_at,
                    user_telegram_login=user_telegram_login,
                    order_id=order_id
                )
                product_info = f"📝 <b>Название услуги:</b> {sale_data.service_name}\n\n👤 <b>Логин клиента:</b> {sale_data.client_login}"
                
            elif isinstance(sale_data, OurProductData):
                sheets_success = self.sheets_service.add_product_sale_record(
                    game_name=sale_data.game_name,
                    console=sale_data.console,
                    position=sale_data.position,
                    ps_login=sale_data.ps_login,
                    comment=sale_data.comment,
                    amount=sale_data.amount,
                    timestamp=sale_data.created_at,
                    user_telegram_login=user_telegram_login,
                    order_id=order_id
                )
                product_info = (
                    f"🎮 <b>Название игры:</b> {sale_data.game_name}\n\n"
                    f"🧩 <b>Консоль:</b> {sale_data.console}\n\n"
                    f"📍 <b>Позиция:</b> {sale_data.position}\n\n"
                    f"👤 <b>PS Login:</b> {sale_data.ps_login}\n\n"
                    f"💬 <b>Комментарий:</b> {sale_data.comment}\n"
                )

            
            # Получаем дополнительную информацию об оплате
            pay_method = status_result.get("pay_method", "")
            pay_data = status_result.get("pay_data", "")
            fee = status_result.get("fee", 0)
            
            success_message = (
                "💙 <b>Платеж успешно оплачен!</b>\n"
                "━━━━━━━━━━━━━━━━\n"
                f"{product_info}\n\n"
                f"💰 <b>Сумма:</b> {sale_data.amount:.2f} ₽\n\n"
                f"💸 <b>Комиссия:</b> {fee:.2f} ₽\n\n"
                f"💳 <b>Получено:</b> {amount_received:.2f} ₽\n\n"
                f"💲 <b>Способ оплаты:</b> {payment_display}\n\n"
                f"🆔 <b>Номер заказа:</b> <code>{order_id}</code>\n\n"
                f"🆔 <b>Идентификатор платежа:</b> <code>{payment_id}</code>\n"
            )
            
            if pay_method and pay_data:
                success_message += f"\n💳 <b>Метод:</b> {pay_method} ({pay_data})\n"
            
            success_message += (
                f"━━━━━━━━━━━━━━━━\n{'☑️ Данные записаны в таблицу.' if sheets_success else '⚠️ Ошибка записи в таблицу.'}\n\n"
                "📊 Заказ сохранен в системе."
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=success_message,
                reply_markup=get_back_to_main_after_sale_keyboard(),
                parse_mode="HTML"
            )
            
            logger.info(f"Платеж {payment_id} успешно обработан и записан в таблицу")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке успешного платежа {payment_id}: {e}")
            
            # Отправляем сообщение об ошибке сохранения
            error_message = (
                "⚠️ <b>Платеж оплачен, но возникла ошибка сохранения</b>\n"
                "━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>Payment ID:</b> <code>{payment_id}</code>\n\n"
                f"💰 <b>Сумма:</b> {sale_data.amount:.2f} ₽\n\n"
                "Обратитесь к администратору для ручного добавления в таблицу."
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=error_message,
                parse_mode="HTML"
            )
    
    async def _handle_failed_payment(self, order_id: str, payment_id: str,
                                   chat_id: int, status: str):
        """Обработка неудачного платежа"""
        status_messages = {
            "FAIL": "❌ Платеж не был оплачен из-за ошибки",
            "CANCEL": "🚫 Платеж был отменен покупателем",
            "EXPIRED": "⏰ Время оплаты истекло"
        }
        
        message = status_messages.get(status, f"❌ Платеж завершился со статусом: {status}")
        
        fail_message = (
            f"{message}\n"
            "━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Номер заказа:</b> <code>{order_id}</code>\n\n"
            f"🆔 <b>Идентификатор платежа:</b> <code>{payment_id}</code>\n\n"

            "Вы можете создать новый платеж."
        )
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=fail_message,
            parse_mode="HTML"
        )
        
        logger.info(f"Платеж {payment_id} завершился неудачно: {status}")
    
    async def _handle_timeout_payment(self, order_id: str, payment_id: str, chat_id: int):
        """Обработка истечения времени ожидания"""
        timeout_message = (
            "⏰ <b>Время ожидания оплаты истекло</b>\n"
            "━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Номер заказа:</b> <code>{order_id}</code>\n\n"
            f"🆔 <b>Идентификатор платежа:</b> <code>{payment_id}</code>\n\n"

            "Проверьте статус платежа вручную или создайте новый."
        )
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=timeout_message,
            parse_mode="HTML"
        )
        
        logger.warning(f"Время ожидания платежа {payment_id} истекло") 