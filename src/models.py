from dataclasses import dataclass
from typing import Optional, Union
from datetime import datetime


@dataclass
class FreeSaleData:
    """Модель данных для свободной продажи"""
    service_name: str
    client_login: str
    comment: str
    amount: float
    user_id: int
    username: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Валидация суммы
        if self.amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")


@dataclass
class OurProductData:
    """Модель данных для продажи нашего товара"""
    game_name: str
    console: str
    position: str
    ps_login: str
    comment: str
    amount: float
    user_id: int
    username: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Валидация суммы
        if self.amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")


def validate_amount(amount_str: str) -> float:
    """
    Валидация и преобразование строки суммы в число
    
    Args:
        amount_str: Строка с суммой
        
    Returns:
        float: Валидная сумма
        
    Raises:
        ValueError: Если сумма невалидна
    """
    try:
        # Заменяем запятую на точку для корректного парсинга
        amount_str = amount_str.replace(',', '.')
        amount = float(amount_str)
        
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        
        # Ограничиваем максимальную сумму (например, 1 миллион)
        if amount > 1_000_000:
            raise ValueError("Сумма слишком большая")
        
        return round(amount, 2)  # Округляем до 2 знаков после запятой
        
    except ValueError as e:
        if "could not convert" in str(e):
            raise ValueError("Введите корректную сумму (например: 1000 или 1000.50)")
        raise e 