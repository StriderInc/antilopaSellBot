"""
Модуль для работы с Google Sheets
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import List, Any, Optional
import logging
from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Класс для работы с Google Sheets"""
    
    def __init__(self):
        self.credentials_file = GOOGLE_CREDENTIALS_FILE
        self.sheet_id = GOOGLE_SHEET_ID
        self.client = None
        self.spreadsheet = None
        
    def _authenticate(self) -> bool:
        """
        Аутентификация в Google Sheets API
        """
        try:
            # Определяем области доступа
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загружаем учетные данные
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, scope
            )
            
            # Авторизуемся
            self.client = gspread.authorize(credentials)
            
            # Открываем таблицу
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            
            logger.info("Успешная аутентификация в Google Sheets")
            return True
            
        except FileNotFoundError:
            logger.error(f"Файл учетных данных не найден: {self.credentials_file}")
            return False
        except gspread.SpreadsheetNotFound:
            logger.error(f"Таблица не найдена: {self.sheet_id}")
            return False
        except Exception as e:
            logger.error(f"Ошибка аутентификации Google Sheets: {e}")
            return False
    
    def _get_or_create_worksheet(self, title: str, headers: List[str]) -> Optional[gspread.Worksheet]:
        """
        Получить или создать лист в таблице
        """
        try:
            # Пытаемся найти существующий лист
            try:
                worksheet = self.spreadsheet.worksheet(title)
                return worksheet
            except gspread.WorksheetNotFound:
                # Создаем новый лист
                worksheet = self.spreadsheet.add_worksheet(
                    title=title, 
                    rows=1000, 
                    cols=len(headers)
                )
                # Добавляем заголовки
                worksheet.append_row(headers)
                logger.info(f"Создан новый лист: {title}")
                return worksheet
                
        except Exception as e:
            logger.error(f"Ошибка при работе с листом {title}: {e}")
            return None
    
    def add_free_sale_record(self, service_name: str, client_login: str, 
                           comment: str, amount: float, timestamp: datetime, user_telegram_login: str, order_id: str) -> bool:
        """
        Добавление записи о свободной продаже
        """
        try:
            # Добавляем отладочную информацию
            logger.info(f"Начинаем запись: service_name='{service_name}', client_login='{client_login}', comment='{comment}', amount={amount}")
            
            # Аутентификация
            if not self._authenticate():
                return False
            
            # Заголовки для листа свободных продаж
            headers = [
                'Название услуги', 
                'Логин клиента',
                'Комментарий',
                'Сумма (₽)',
                'Менеджер',
                "Номер заказа",
                'Дата и время',
            ]
            
            # Получаем или создаем лист
            worksheet = self._get_or_create_worksheet('Свободные продажи', headers)
            if not worksheet:
                logger.error("Не удалось получить worksheet")
                return False
            
            # Подготавливаем данные для записи
            row_data = [
                str(service_name),  # Явно преобразуем в строку
                str(client_login),  # Явно преобразуем в строку
                str(comment),       # Явно преобразуем в строку
                float(amount),       # Явно преобразуем в число
                str(user_telegram_login),
                timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                str(order_id),
            ]
            
            # Добавляем отладочную информацию о данных
            logger.info(f"Данные для записи: {row_data}")
            
            # Добавляем строку
            worksheet.append_row(row_data)
            
            logger.info(f"Записана свободная продажа: {service_name}, {amount} ₽")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи свободной продажи: {e}")
            import traceback
            logger.error(f"Полная ошибка: {traceback.format_exc()}")
            return False
    
    def add_product_sale_record(self, game_name: str, console: str, position: str,
                               ps_login: str, comment: str, amount: float, 
                               timestamp: datetime, user_telegram_login: str, order_id: str) -> bool:
        """
        Добавление записи о продаже товара
        """
        try:
            # Аутентификация
            if not self._authenticate():
                return False
            
            # Заголовки для листа продаж товаров
            headers = [
                'Название игры',
                'Консоль',
                'Позиция',
                'Логин PS',
                'Комментарий',
                'Сумма (₽)',
                'Менеджер',
                "Номер заказа",
                'Дата и время',
            ]
            
            # Получаем или создаем лист
            worksheet = self._get_or_create_worksheet('Продажи товаров', headers)
            if not worksheet:
                return False
            
            # Подготавливаем данные для записи
            row_data = [
                game_name,
                console,
                position,
                ps_login,
                comment,
                amount,
                user_telegram_login,
                timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                order_id,
            ]
            
            # Добавляем строку
            worksheet.append_row(row_data)
            
            logger.info(f"Записана продажа товара: {game_name}, {console}, {amount} ₽")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи продажи товара: {e}")
            return False
    
    def get_sales_summary(self, date_from: datetime = None) -> dict:
        """
        Получение сводки по продажам (дополнительный метод)
        """
        try:
            if not self._authenticate():
                return {}
            
            summary = {
                'free_sales_count': 0,
                'free_sales_amount': 0.0,
                'product_sales_count': 0,
                'product_sales_amount': 0.0
            }
            
            # Анализируем свободные продажи
            try:
                free_sales_sheet = self.spreadsheet.worksheet('Свободные продажи')
                free_sales_data = free_sales_sheet.get_all_records()
                
                for row in free_sales_data:
                    summary['free_sales_count'] += 1
                    summary['free_sales_amount'] += float(row.get('Сумма (₽)', 0))
                    
            except gspread.WorksheetNotFound:
                pass
            
            # Анализируем продажи товаров
            try:
                product_sales_sheet = self.spreadsheet.worksheet('Продажи товаров')
                product_sales_data = product_sales_sheet.get_all_records()
                
                for row in product_sales_data:
                    summary['product_sales_count'] += 1
                    summary['product_sales_amount'] += float(row.get('Сумма (₽)', 0))
                    
            except gspread.WorksheetNotFound:
                pass
            
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки: {e}")
            return {} 