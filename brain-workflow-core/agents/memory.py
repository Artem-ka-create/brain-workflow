# agents/memory.py
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
import json


class MemoryManager:
    """
    Керує memory для autonomous agent:
    - Зберігає execution context
    - Summarizes великі результати
    - Надає релевантний контекст для кожного step
    """

    def __init__(self, max_context_length: int = 3000):
        self.context: Dict[str, Any] = {}
        self.summaries: Dict[str, str] = {}  # Короткі версії для великих результатів
        self.max_length = max_context_length
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def store(self, key: str, value: Any):
        """
        Зберігає результат у context.
        Якщо занадто великий - створює summary.
        """
        self.context[key] = value

        # Якщо результат великий - створи summary
        value_str = str(value)
        if len(value_str) > self.max_length:
            print(f"  📝 Creating summary for '{key}' ({len(value_str)} chars)")
            summary = self._create_summary(key, value_str)
            self.summaries[key] = summary

    def get(self, key: str) -> Any:
        """Отримати повний результат"""
        return self.context.get(key)

    def get_for_context(self, key: str) -> Any:
        """
        Отримати результат для передачі в LLM context.
        Якщо є summary - повертає його замість повного результату.
        """
        if key in self.summaries:
            return {
                "_summary": self.summaries[key],
                "_full_available": True,
                "_preview": str(self.context[key])[:200] + "..."
            }
        return self.context.get(key)

    def get_relevant_context(self, required_keys: List[str]) -> Dict[str, Any]:
        """
        Отримати тільки релевантний контекст для step.
        Використовує summaries де можливо.
        """
        relevant = {}
        for key in required_keys:
            if key in self.context:
                relevant[key] = self.get_for_context(key)
        return relevant

    def get_all_keys(self) -> List[str]:
        """Список всіх збережених ключів"""
        return list(self.context.keys())

    def _create_summary(self, key: str, content: str) -> str:
        """Створює короткий summary великого результату"""
        prompt = f"""
Summarize this content concisely (max 300 words). Focus on key information that would be useful for subsequent tasks.

Content from '{key}':
{content[:5000]}  

Provide a structured summary:
"""
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def get_context_stats(self) -> Dict[str, Any]:
        """Статистика про поточний context"""
        total_size = sum(len(str(v)) for v in self.context.values())
        return {
            "total_keys": len(self.context),
            "total_size_chars": total_size,
            "summarized_keys": len(self.summaries),
            "keys": list(self.context.keys())
        }


class ConversationMemory:
    """
    Зберігає історію розмови для multi-turn взаємодії.
    Потрібно якщо хочеш щоб agent міг відповідати на follow-up питання.
    """

    def __init__(self, max_turns: int = 10):
        self.messages: List[Dict[str, str]] = []
        self.max_turns = max_turns

    def add_user_message(self, content: str):
        """Додати повідомлення користувача"""
        self.messages.append({
            "role": "user",
            "content": content
        })
        self._trim_history()

    def add_agent_message(self, content: str):
        """Додати відповідь агента"""
        self.messages.append({
            "role": "assistant",
            "content": content
        })
        self._trim_history()

    def get_history(self, last_n: int = None) -> List[Dict[str, str]]:
        """Отримати історію розмови"""
        if last_n:
            return self.messages[-last_n:]
        return self.messages

    def _trim_history(self):
        """Обрізати історію якщо занадто довга"""
        if len(self.messages) > self.max_turns * 2:
            # Залиш перше повідомлення (original goal) + останні N
            self.messages = [self.messages[0]] + self.messages[-(self.max_turns * 2):]

    def clear(self):
        """Очистити історію"""
        self.messages = []


# ==================== INTEGRATION HELPERS ====================

def create_memory_aware_context(
        memory: MemoryManager,
        required_keys: List[str]
) -> Dict[str, Any]:
    """
    Helper функція для створення контексту з memory для ReAct agent.
    Автоматично використовує summaries де треба.
    """
    context = memory.get_relevant_context(required_keys)

    # Додай meta-info
    context["_available_keys"] = memory.get_all_keys()
    context["_memory_stats"] = memory.get_context_stats()

    return context