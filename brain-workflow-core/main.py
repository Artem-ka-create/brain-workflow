# main.py - Головний файл що зв'язує все разом
import os
from turtle import pd
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from agents.planner import create_plan
from agents.evaluator import evaluate_plan
from agents.executor import Executor, ToolRegistry
from agents.observer import simple_observer
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper

load_dotenv()
llm = ChatOpenAI(model="gpt-5-mini", temperature=0)

# ==================== TOOLS SETUP ====================

def setup_tools() -> ToolRegistry:
    """Реєструє всі доступні tools"""
    tools = ToolRegistry()

    # Tool 1: Web Search (mock for now, replace with real implementation)
    serp_api = GoogleSerperAPIWrapper()  # auth via .env automatically

    def web_search(params: Dict[str, Any]):
        print("PARAMS-> ",params)
        query = params.get("query", "")
        if not query:
            return {"error": "missing 'query' in parameters"}

        print(f"[web_search] Searching: {query}")
        result = serp_api.run(query)  # Returns summarized results
        return {"query": query, "results": result}

    # Tool 2: Code Executor (mock)
    def code_executor(params):
        code = params.get("code", "")
        language = params.get("language", "python")
        print(f"    [code_executor] Executing {language} code")
        # TODO: Replace with real code execution
        return {
            "language": language,
            "output": f"Mock execution result for code: {code[:50]}..."
        }

    # Tool 3: File Write
    def file_write(params):
        filename = params.get("filename", "output.txt")
        content = params.get("content", "")
        print(f"    [file_write] Writing to {filename}")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "filename": filename, "bytes": len(content)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Tool 4: Data Analysis (mock)
    def data_analysis(params: Dict[str, Any]):
        print("PARAMS-> ",params)
        # PARAMS->  {'context_data': ['recommended_methods', 'learning_preference']}
        """
        Supported params:
        - data: list of dicts OR CSV string OR JSON string
        - analysis_type: summary | correlation | outliers | llm_insights | auto
        """

        data = params.get("data", None)
        analysis_type = params.get("analysis_type", "summary")

        print(f"[data_analysis] Data analysis type: {analysis_type}")
        print(f"[data_analysis] Data analysis data: {data}")

        if data is None:
            return {"error": "Missing 'data' parameter"}

        # ======================
        # 1) PARSE DATA INTO PANDAS
        # ======================
        try:
            if isinstance(data, str):
                if data.strip().startswith("["):
                    df = pd.read_json(data)
                else:
                    from io import StringIO
                    df = pd.read_csv(StringIO(data))
            else:
                df = pd.DataFrame(data)  # list of dicts or similar
        except Exception as e:
            return {"error": f"Could not convert to DataFrame: {e}"}

        response = {"analysis_type": analysis_type, "rows": len(df), "cols": list(df.columns)}

        # ======================
        # 2) ANALYSIS LOGIC
        # ======================
        if analysis_type == "summary":
            response["summary"] = df.describe(include="all").to_dict()

        elif analysis_type == "correlation":
            response["correlation"] = df.corr(numeric_only=True).to_dict()

        elif analysis_type == "outliers":
            numeric_df = df.select_dtypes(include=["int64", "float64"])
            outliers = (numeric_df - numeric_df.mean()).abs() > (3 * numeric_df.std())
            response["outliers"] = outliers.sum().to_dict()

        elif analysis_type == "llm_insights":
            prompt = f"Analyze this data and provide key insights:\n\n{df.head().to_string()}"
            llm_output = llm.invoke(prompt)
            response["llm_insights"] = llm_output.content

        elif analysis_type == "auto":
            # decide automatically
            if len(df.columns) > 4:
                response["auto_decision"] = "correlation"
                response["correlation"] = df.corr(numeric_only=True).to_dict()
            else:
                response["auto_decision"] = "summary"
                response["summary"] = df.describe(include="all").to_dict()

        else:
            response["error"] = f"Unknown analysis_type: {analysis_type}"

        return response

    # Реєструємо tools
    tools.register("web_search", web_search)
    tools.register("code_executor", code_executor)
    tools.register("file_write", file_write)
    tools.register("data_analysis", data_analysis)

    return tools


# ==================== MAIN ORCHESTRATOR ====================

class AutonomousAgent:
    """
    Головний клас що об'єднує всі компоненти:
    Planner → Evaluator → Executor (with ReAct) → Observer
    """

    def __init__(self):
        self.tools = setup_tools()
        print(f"✅ Tools registered: {self.tools.list_tools()}")

    def run(self, user_goal: str):
        """
        Головний метод що виконує повний цикл:
        1. Planner створює план
        2. Evaluator перевіряє план
        3. Executor виконує план (з ReAct агентом)
        4. Observer відслідковує прогрес
        """

        print("\n" + "=" * 70)
        print("🚀 AUTONOMOUS AI AGENT - START")
        print("=" * 70)
        print(f"User Goal: {user_goal}\n")

        # ========== STEP 1: PLANNING ==========
        print("\n" + "🎯 PHASE 1: PLANNING" + "\n" + "-" * 70)
        plan = create_plan(user_goal)

        print(f"✅ Plan created with {len(plan.steps)} steps:")
        for i, step in enumerate(plan.steps):
            print(f"  {i + 1}. [{step.stage}] {step.title}")

        # Show full plan JSON
        print("\n📄 Full Plan JSON:")
        print("-" * 70)
        print(plan.model_dump_json(indent=2))
        print("-" * 70)

        # ========== STEP 2: EVALUATION ==========
        print("\n" + "🔍 PHASE 2: PLAN EVALUATION" + "\n" + "-" * 70)
        eval_result = evaluate_plan(user_goal, plan)

        print(f"Verdict: {eval_result.verdict}")

        if not eval_result.is_good and eval_result.improved_plan:
            print("⚠️  Plan was improved by evaluator")
            plan = eval_result.improved_plan
            print(f"✅ Using improved plan with {len(plan.steps)} steps")
        else:
            print("✅ Plan approved")

        # ========== STEP 3: EXECUTION ==========
        print("\n" + "⚙️  PHASE 3: EXECUTION (with ReAct Agent)" + "\n" + "-" * 70)

        # Створюємо executor з ReAct агентом
        executor = Executor(
            tools=self.tools,
            ask_user=self._ask_user,
            observer=simple_observer
        )

        # Виконуємо план
        try:
            executor.run_plan(plan)
        except Exception as e:
            print(f"\n❌ Execution error: {e}")
            return None

        # ========== STEP 4: RESULTS ==========
        print("\n" + "📊 PHASE 4: RESULTS" + "\n" + "-" * 70)
        self._display_results(executor.context, plan)

        print("\n" + "=" * 70)
        print("✅ AUTONOMOUS AI AGENT - COMPLETE")
        print("=" * 70 + "\n")

        return executor.context

    def _ask_user(self, question: str) -> str:
        """Функція для збору інформації від користувача"""
        print(f"\n❓ {question}")
        answer = input("👉 Your answer: ")
        return answer

    def _display_results(self, context: dict, plan):
        """Показує фінальні результати"""
        print("\n📋 Execution Context (all results):")
        for key, value in context.items():
            if key == "original_goal":
                continue
            print(f"\n  [{key}]")
            value_str = str(value)
            if len(value_str) > 200:
                print(f"    {value_str[:200]}...")
            else:
                print(f"    {value_str}")

        # Фінальний результат
        final_keys = [step.output_key or step.id for step in plan.steps if step.stage == "action"]
        if final_keys:
            final_key = final_keys[-1]  # Останній action step
            if final_key in context:
                print(f"\n🎯 FINAL RESULT (from '{final_key}'):")
                print("-" * 70)
                print(context[final_key])
                print("-" * 70)


# ==================== USAGE EXAMPLES ====================

def example_simple():
    """Простий приклад"""
    agent = AutonomousAgent()

    goal = "Create a simple Python script that calculates fibonacci numbers"
    agent.run(goal)


def example_research():
    """Приклад з research"""
    agent = AutonomousAgent()

    goal = "Research the latest AI trends in 2024 and create a summary report"
    agent.run(goal)


def example_learning_plan():
    """Приклад зі створенням плану навчання"""
    agent = AutonomousAgent()

    goal = "Create a learning plan for learning Chinese from zero to B2 level"
    agent.run(goal)


# ==================== MAIN ====================

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         AUTONOMOUS AI AGENT - Hackathon Demo              ║
    ║                                                            ║
    ║  Architecture:                                             ║
    ║  1. Planner Agent → Creates high-level plan               ║
    ║  2. Evaluator → Validates & improves plan                 ║
    ║  3. Orchestrator → Manages execution                      ║
    ║  4. ReAct Agent → Autonomous execution with reasoning     ║
    ║  5. Observer → Monitors global goal achievement           ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Вибери один з прикладів або введи свій goal

    # Приклад 1: Простий
    # example_simple()

    # Приклад 2: Research
    # example_research()

    # Приклад 3: Кастомний goal
    agent = AutonomousAgent()

    print("\n💬 Enter your goal (or press Enter for default):")
    user_goal = input("👉 ").strip()

    if not user_goal:
        user_goal = "Research Python best practices and create a cheat sheet"
        print(f"Using default goal: {user_goal}")

    # Clean encoding issues
    user_goal = user_goal.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    user_goal = ''.join(char for char in user_goal if ord(char) < 0x10000)

    agent.run(user_goal)