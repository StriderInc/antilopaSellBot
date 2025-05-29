from aiogram.fsm.state import State, StatesGroup


class FreeSaleStates(StatesGroup):
    """Состояния для свободной продажи"""
    waiting_service_name = State()
    waiting_client_login = State()
    waiting_comment = State()
    waiting_amount = State()
    confirmation = State()
    payment_method_selection = State()
    final_confirmation = State()


class OurProductStates(StatesGroup):
    """Состояния для продажи нашего товара"""
    waiting_game_name = State()
    choosing_console = State()
    choosing_position = State()
    waiting_ps_login = State()
    waiting_comment = State()
    waiting_amount = State()
    confirmation = State()
    payment_method_selection = State()
    final_confirmation = State() 