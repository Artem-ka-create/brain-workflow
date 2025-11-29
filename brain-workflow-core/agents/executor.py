# agents/executor.py
from typing import Callable, Dict, Any
from .models import Plan, Step
from dotenv import load_dotenv

load_dotenv()


# Простий реєстр тулів
ToolFn = Callable[[Dict[str, Any]], Any]


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolFn] = {}

    def register(self, name: str, fn: ToolFn):
        self._tools[name] = fn

    def call(self, name: str, params: Dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered")
        return self._tools[name](params)


class Executor:
    def __init__(
        self,
        tools: ToolRegistry,
        ask_user: Callable[[str], str],
        observer: Callable[[Plan, int, Dict[str, Any]], bool],
    ):
        """
        ask_user: function that asks user a question and returns answer string.
        observer: returns True if execution should stop (goal reached), else False.
        """
        self.tools = tools
        self.ask_user = ask_user
        self.observer = observer
        self.context: Dict[str, Any] = {}

    def run_plan(self, plan: Plan):
        steps = plan.steps

        for idx, step in enumerate(steps):
            print(f"\n[STEP {idx+1}/{len(steps)}] {step.title} ({step.stage})")

            if step.stage == "question":
                self._run_question_step(step)
            elif step.stage == "analysis":
                self._run_analysis_step(step)
            elif step.stage == "action":
                self._run_action_step(step)
            else:
                raise ValueError(f"Unknown stage {step.stage}")

            # Observer перевіряє, чи закінчуємо
            stop = self.observer(plan, idx, self.context)
            if stop:
                print("[OBSERVER] Goal considered complete. Stopping execution.")
                break

    # --- окремі режими виконання ---

    def _run_question_step(self, step: Step):
        question_text = step.instruction
        answer = self.ask_user(question_text)
        key = step.output_key or step.id
        self.context[key] = answer

    def _run_analysis_step(self, step: Step):
        # тут можна підключити LLM-аналіз (спрощений stub)
        # наприклад: llm.invoke({"instruction": step.instruction, "context": self.context})
        print("[ANALYSIS] (stub) using context keys:", list(self.context.keys()))
        self.context[step.output_key or step.id] = {
            "note": "analysis would be done here using LLM and context"
        }

    def _run_action_step(self, step: Step):
        if step.tool:
            params = {k: self.context.get(k) for k in step.expected_input_keys}
            result = self.tools.call(step.tool, params)
            self.context[step.output_key or step.id] = result
        else:
            # Напр., просто генерувати текстовий план тренувань у майбутній версії
            print("[ACTION] No tool defined, nothing executed yet.")
