"""
Модуль для работы с Antilopay API
"""

import json
import base64
import hashlib
import uuid
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from config import (
    ANTILOPAY_API_URL, 
    ANTILOPAY_PROJECT_ID, 
    ANTILOPAY_SECRET_ID, 
    ANTILOPAY_PRIVATE_KEY
)

logger = logging.getLogger(__name__)


class AntilopayAPI:
    """Класс для работы с Antilopay API"""
    
    def __init__(self):
        self.api_url = ANTILOPAY_API_URL.rstrip('/')
        self.project_id = ANTILOPAY_PROJECT_ID
        self.secret_id = ANTILOPAY_SECRET_ID
        self.private_key = ANTILOPAY_PRIVATE_KEY
        
    def _generate_signature(self, payload: str) -> str:
        """
        Генерация RSA подписи SHA256WithRSA согласно документации
        """
        try:
            # Декодируем приватный ключ из Base64
            rsa_key = RSA.importKey(base64.b64decode(self.private_key))
            
            # Создаем хеш SHA256 от payload
            payload_bytes = bytes(payload, 'UTF-8')
            hash_obj = SHA256.new(payload_bytes)
            
            # Создаем подпись
            signature = pkcs1_15.new(rsa_key).sign(hash_obj)
            
            # Кодируем в Base64
            return base64.b64encode(signature).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Ошибка генерации подписи: {e}")
            raise
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение запроса к API с подписью
        """
        try:
            # Формируем JSON payload без пробелов и переносов
            payload = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            
            # Генерируем подпись
            signature = self._generate_signature(payload)
            
            # Формируем заголовки
            headers = {
                'Content-Type': 'application/json',
                'X-Apay-Secret-Id': self.secret_id,
                'X-Apay-Sign': signature,
                'X-Apay-Sign-Version': '1'
            }
            
            # Выполняем запрос
            url = f"{self.api_url}/{endpoint}"
            logger.info(f"Отправка запроса к {url}")
            
            response = requests.post(
                url, 
                data=payload.encode('utf-8'), 
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Ответ API: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"HTTP ошибка: {response.status_code}, {response.text}")
                return {
                    "code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса: {e}")
            return {"code": 500, "error": f"Ошибка сети: {str(e)}"}
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return {"code": 500, "error": f"Внутренняя ошибка: {str(e)}"}
    
    def create_payment(self, amount: float, product_name: str, client_login: str,
                      description: str, prefer_methods: list = None) -> Dict[str, Any]:
        """
        Создание платежа согласно ТЗ и документации Antilopay
        
        Args:
            amount: Сумма платежа
            product_name: Название товара/услуги
            description: Описание платежа
            prefer_methods: Предпочтительные методы оплаты ["CARD_RU", "SBER_PAY", "SBP"]
        """
        try:
            order_id = str(uuid.uuid4())
            # Формируем данные запроса согласно ТЗ
            payment_data = {
                "project_identificator": self.project_id,
                "amount": float(amount),
                "order_id": order_id,
                "currency": "RUB",
                "product_name": product_name,
                "product_type": "goods",
                "description": description,
                "customer": {
                    "email": client_login
                }
            }
            
            # Добавляем методы оплаты если указаны
            if prefer_methods:
                payment_data["prefer_methods"] = prefer_methods
            
            logger.info(f"Создание платежа: {order_id}, сумма: {amount} ₽, методы: {prefer_methods}")
            
            # Выполняем запрос
            response = self._make_request("payment/create", payment_data)
            
            if response.get("code") == 0:
                logger.info(f"Платеж создан успешно: {response.get('payment_id')}")
                return {
                    "success": True,
                    "payment_id": response.get("payment_id"),
                    "payment_url": response.get("payment_url"),
                    "order_id": order_id,
                    "amount": amount
                }
            else:
                logger.error(f"Ошибка создания платежа: {response}")
                return {
                    "success": False,
                    "error": response.get("error", "Неизвестная ошибка"),
                    "code": response.get("code")
                }
                
        except Exception as e:
            logger.error(f"Исключение при создании платежа: {e}")
            return {
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }
    
    def check_payment_status(self, order_id: str) -> Dict[str, Any]:
        """
        Проверка статуса платежа
        """
        try:
            check_data = {
                "project_identificator": self.project_id,
                "order_id": order_id
            }
            
            logger.info(f"Проверка статуса платежа: {order_id}")
            
            response = self._make_request("payment/check", check_data)
            
            if response.get("code") == 0:
                return {
                    "success": True,
                    "payment_id": response.get("payment_id"),
                    "order_id": response.get("order_id"),
                    "status": response.get("status"),
                    "amount": response.get("amount"),
                    "original_amount": response.get("original_amount"),
                    "fee": response.get("fee"),
                    "currency": response.get("currency"),
                    "payment_url": response.get("payment_url"),
                    "pay_method": response.get("pay_method"),
                    "pay_data": response.get("pay_data"),
                    "ctime": response.get("ctime"),
                    "product_name": response.get("product_name"),
                    "description": response.get("description"),
                    "customer": response.get("customer")
                }
            else:
                logger.error(f"Ошибка проверки статуса: {response}")
                return {
                    "success": False,
                    "error": response.get("error", "Неизвестная ошибка"),
                    "code": response.get("code")
                }
                
        except Exception as e:
            logger.error(f"Исключение при проверке статуса: {e}")
            return {
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }