from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CONSOLES


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню выбора типа продажи"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🆓 Свободная продажа", callback_data="free_sale"),
        InlineKeyboardButton(text="🎮 Продажа нашего товара", callback_data="our_product")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_console_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора консоли"""
    builder = InlineKeyboardBuilder()
    for console in CONSOLES.keys():
        builder.add(InlineKeyboardButton(text=console, callback_data=f"console_{console}"))
    builder.add(InlineKeyboardButton(text="❌ Отменить операцию", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def get_console_keyboard_with_back() -> InlineKeyboardMarkup:
    """Клавиатура выбора консоли с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки консолей
    for console in CONSOLES.keys():
        builder.add(InlineKeyboardButton(text=console, callback_data=f"console_{console}"))
    
    # Добавляем кнопки навигации
    builder.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_game_name"),
        InlineKeyboardButton(text="❌ Отменить операцию", callback_data="cancel")
    )
    
    # Настраиваем расположение: консоли по одной в ряд, затем навигация в два столбца
    console_count = len(CONSOLES)
    builder.adjust(*([1] * console_count), 2)  # Консоли по 1, навигация по 2
    
    return builder.as_markup()


def get_position_keyboard(console: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора позиции для консоли"""
    builder = InlineKeyboardBuilder()
    positions = CONSOLES.get(console, [])
    for position in positions:
        builder.add(InlineKeyboardButton(text=position, callback_data=f"position_{console}_{position}"))
    builder.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_console"),
        InlineKeyboardButton(text="❌ Отменить операцию", callback_data="cancel")
    )
    builder.adjust(1, 2)  # Позиции в один столбец, кнопки назад/отменить в два столбца
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения данных"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
        InlineKeyboardButton(text="🔄 Изменить", callback_data="edit")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main"))
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены операции"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить операцию", callback_data="cancel"))
    return builder.as_markup()


def get_cancel_and_back_keyboard(back_callback: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопками назад и отменить"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback),
        InlineKeyboardButton(text="❌ Отменить операцию", callback_data="cancel")
    )
    builder.adjust(2)
    return builder.as_markup() 