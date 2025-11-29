# agents/observer.py
from typing import Dict, Any
from .models import Plan
from dotenv import load_dotenv

load_dotenv()


def simple_observer(plan: Plan, step_index: int, context: Dict[str, Any]) -> bool:
    """
    Дуже простий варіант:
    - якщо це останній крок → сказати "кінець"
    - можна додати логіку: якщо з'явився ключ 'final_workout_plan' у context → завершити
    """
    is_last = step_index == len(plan.steps) - 1
    if is_last:
        return True

    # приклад додаткової умови
    if "final_workout_plan" in context:
        return True

    return False
