# agents/executor.py
from typing import Callable, Dict, Any, List
from .models import Plan, Step
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json

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

    def list_tools(self) -> List[str]:
        """Повертає список доступних tools"""
        return list(self._tools.keys())


class ReactAgent:
    """
    Autonomous ReAct Agent: Reason → Act → Observe → Evaluate
    """

    def __init__(self, tools_registry: ToolRegistry, llm_model="gpt-4o-mini"):
        self.tools = tools_registry
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        self.max_iterations = 10

    def execute_step(self, step: Step, global_context: Dict[str, Any]) -> Any:
        """
        Виконує один step автономно використовуючи ReAct loop
        """
        print(f"\n{'=' * 60}")
        print(f"🤖 ReAct Agent executing: {step.title}")
        print(f"{'=' * 60}")

        # Пам'ять агента для цього step
        agent_memory = {
            "step": step,
            "available_context": {k: v for k, v in global_context.items()
                                  if k in step.expected_input_keys},
            "thought_log": [],
            "action_log": []
        }

        for iteration in range(self.max_iterations):
            print(f"\n--- Iteration {iteration + 1}/{self.max_iterations} ---")

            # 1. THINK (Reasoning)
            thought = self._reason(agent_memory, iteration)
            agent_memory["thought_log"].append({
                "iteration": iteration,
                "thought": thought
            })
            print(f"💭 THOUGHT: {thought[:250]}...")

            # 2. DECIDE ACTION
            action = self._decide_action(thought, agent_memory)

            if action["type"] == "final_answer":
                print(f"✅ Agent decided task is complete")
                return action["answer"]

            # 3. ACT (Execute)
            print(f"🔧 ACTION: Using tool '{action.get('tool', 'N/A')}'")
            result = self._execute_action(action)

            # 4. OBSERVE
            observation = self._observe(result, step)
            agent_memory["action_log"].append({
                "iteration": iteration,
                "action": action,
                "result": str(result)[:500],  # обрізаємо для контексту
                "observation": observation
            })
            print(f"👁️  OBSERVATION: {observation[:200]}...")

            # 5. EVALUATE
            is_complete = self._evaluate_completion(step, agent_memory)
            if is_complete:
                print(f"✅ Step completed in {iteration + 1} iterations")
                return self._synthesize_final_result(step, agent_memory)

        # Fallback якщо не закінчилось
        print(f"⚠️  Max iterations reached. Synthesizing best available result.")
        return self._synthesize_final_result(step, agent_memory)

    def _reason(self, memory: Dict, iteration: int) -> str:
        """Крок 1: Reasoning - що робити далі?"""
        step = memory["step"]
        recent_thoughts = memory["thought_log"][-2:]
        recent_actions = memory["action_log"][-2:]

        prompt = f"""
You are an autonomous agent executing this task:

INSTRUCTION: {step.instruction}
STAGE: {step.stage}
ITERATION: {iteration + 1}/{self.max_iterations}

AVAILABLE TOOLS:
{json.dumps(self.tools.list_tools(), indent=2)}

CONTEXT DATA AVAILABLE:
{json.dumps(list(memory["available_context"].keys()), indent=2)}

RECENT THOUGHTS:
{json.dumps(recent_thoughts, indent=2)}

RECENT ACTIONS & OBSERVATIONS:
{json.dumps(recent_actions, indent=2)}

Think step by step:
1. What have I accomplished so far?
2. What information do I still need to complete this task?
3. What should I do next?
4. Do I have enough to provide a final answer?

Provide your reasoning (2-4 sentences):
"""
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def _decide_action(self, thought: str, memory: Dict) -> Dict:
        """Крок 2: Вибрати конкретну дію на основі reasoning"""
        step = memory["step"]

        prompt = f"""
Based on this reasoning:
{thought}

TASK: {step.instruction}
AVAILABLE TOOLS: {self.tools.list_tools()}
AVAILABLE CONTEXT: {list(memory["available_context"].keys())}

Decide the next action. Return ONLY valid JSON in one of these formats:

Option 1 - Use a tool:
{{
  "type": "use_tool",
  "tool": "tool_name",
  "params": {{"key": "value"}}
}}

Option 2 - Task complete:
{{
  "type": "final_answer",
  "answer": "the synthesized result or conclusion"
}}

Return ONLY the JSON, nothing else:
"""
        response = self.llm.invoke(prompt).content.strip()

        # Parse JSON
        try:
            # Витягни JSON якщо обгорнутий у markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except Exception as e:
            print(f"⚠️  Failed to parse action decision: {e}")
            print(f"Raw response: {response[:200]}")

            # Fallback: якщо є tool в step definition
            if step.tool:
                params = {k: memory["available_context"].get(k)
                          for k in step.expected_input_keys}
                return {
                    "type": "use_tool",
                    "tool": step.tool,
                    "params": params
                }

            # Останній fallback
            return {
                "type": "final_answer",
                "answer": "Unable to complete task due to parsing error"
            }

    def _execute_action(self, action: Dict) -> Any:
        """Крок 3: Виконати вибрану дію"""
        if action["type"] == "use_tool":
            try:
                tool_name = action["tool"]
                params = action.get("params", {})
                result = self.tools.call(tool_name, params)
                return result
            except Exception as e:
                return {"error": str(e), "tool": action["tool"]}
        return None

    def _observe(self, result: Any, step: Step) -> str:
        """Крок 4: Спостереження - що показав результат?"""
        prompt = f"""
You just executed an action as part of this task: {step.instruction}

Action result:
{str(result)[:1000]}

What does this result tell us? What useful information did we gain?
Provide a brief observation (1-3 sentences):
"""
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def _evaluate_completion(self, step: Step, memory: Dict) -> bool:
        """Крок 5: Оцінити чи task завершений"""
        recent_thoughts = memory["thought_log"][-2:]
        recent_actions = memory["action_log"][-2:]

        prompt = f"""
TASK: {step.instruction}

RECENT REASONING:
{json.dumps(recent_thoughts, indent=2)}

RECENT ACTIONS & OBSERVATIONS:
{json.dumps(recent_actions, indent=2)}

Question: Is this task complete? Do we have sufficient information to provide a final answer?

Answer with ONLY "YES" or "NO" followed by a one-sentence reason:
Example: "YES - We have gathered all required data and can now synthesize the final result."
"""
        response = self.llm.invoke(prompt).content.strip()

        # Перевір чи починається з YES
        is_complete = response.upper().startswith("YES")
        print(f"🔍 EVALUATION: {response[:150]}")

        return is_complete

    def _synthesize_final_result(self, step: Step, memory: Dict) -> Any:
        """Синтезувати фінальний результат з усіх спостережень"""
        prompt = f"""
Task: {step.instruction}

All thoughts and reasoning:
{json.dumps(memory["thought_log"], indent=2)}

All actions and observations:
{json.dumps(memory["action_log"], indent=2)}

Synthesize all of this into a clear, structured final result that answers the task.
Be concise but complete. Format appropriately (text, list, structured data, etc.):
"""
        response = self.llm.invoke(prompt)
        return response.content.strip()


class Executor:
    """
    Orchestrator що керує виконанням плану
    """

    def __init__(
            self,
            tools: ToolRegistry,
            ask_user: Callable[[str], str],
            observer: Callable[[Plan, int, Dict[str, Any]], bool],
    ):
        """
        ask_user: функція що задає питання користувачу
        observer: перевіряє чи досягнута глобальна ціль
        """
        self.tools = tools
        self.ask_user = ask_user
        self.observer = observer
        self.context: Dict[str, Any] = {}

        # Ініціалізуємо ReAct агента
        self.react_agent = ReactAgent(tools)

    def run_plan(self, plan: Plan):
        """Виконує план step-by-step"""
        steps = plan.steps

        for idx, step in enumerate(steps):
            print(f"\n{'#' * 60}")
            print(f"[STEP {idx + 1}/{len(steps)}] {step.title} ({step.stage})")
            print(f"{'#' * 60}")

            # Виконай step відповідно до його stage
            if step.stage == "question":
                self._run_question_step(step)
            elif step.stage == "analysis":
                self._run_analysis_step(step)
            elif step.stage == "action":
                self._run_action_step(step)
            else:
                raise ValueError(f"Unknown stage: {step.stage}")

            # Observer перевіряє чи досягли глобальної цілі
            stop = self.observer(plan, idx, self.context)
            if stop:
                print("\n🎯 [OBSERVER] Global goal achieved. Stopping execution.")
                break

    def _run_question_step(self, step: Step):
        """Збір інформації від користувача"""
        print(f"\n❓ Question: {step.instruction}\n")
        answer = self.ask_user(step.instruction)
        key = step.output_key or step.id
        self.context[key] = answer
        print(f"✅ Saved answer to context['{key}']")

    def _run_analysis_step(self, step: Step):
        """Аналіз даних використовуючи LLM"""
        print(f"\n🔍 Analysis: {step.instruction}")

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Підготуй контекст для аналізу
        relevant_context = {k: self.context.get(k)
                            for k in step.expected_input_keys
                            if k in self.context}

        prompt = f"""
You are performing analysis as part of a larger autonomous task.

ANALYSIS INSTRUCTION:
{step.instruction}

AVAILABLE DATA:
{json.dumps(relevant_context, indent=2)}

Perform the requested analysis and provide structured results:
"""

        response = llm.invoke(prompt)
        result = response.content

        key = step.output_key or step.id
        self.context[key] = result

        print(f"✅ Analysis complete. Saved to context['{key}']")
        print(f"Result preview: {result[:200]}...")

    def _run_action_step(self, step: Step):
        """Виконання action через ReAct агента"""
        # ReAct агент автономно виконує step
        result = self.react_agent.execute_step(step, self.context)

        # Збережи результат у контекст
        key = step.output_key or step.id
        self.context[key] = result

        print(f"\n✅ Action complete. Result saved to context['{key}']")