# main.py
from agents.planner import create_plan
from agents.evaluator import evaluate_plan
from agents.executor import Executor, ToolRegistry
from agents.observer import simple_observer
from dotenv import load_dotenv

load_dotenv()

def ask_user_cli(question: str) -> str:
    print(f"[QUESTION] {question}")
    return input("> ")


# Приклад тулу: stub, який створює текст тренування
def generate_workout_tool(params):
    # тут ти потім підключиш LLM / свою логіку
    level = params.get("experience_level", "unknown level")
    return f"Sample workout plan for {level} (tool stub)"


def main():
    user_goal = input("Введи ціль по тренуванням:\n> ")

    # 1) план
    plan = create_plan(user_goal)
    print("\n[RAW PLAN JSON]")
    print(plan.model_dump_json(indent=2))

    # 2) евалюатор
    eval_result = evaluate_plan(user_goal, plan)
    print("\n[EVAL VERDICT]", eval_result.verdict)

    if not eval_result.is_good and eval_result.improved_plan:
        plan = eval_result.improved_plan
        print("\n[PLAN WAS IMPROVED BY EVALUATOR]")
        print(plan.model_dump_json(indent=2))

    # 3) реєструємо тулзи
    tools = ToolRegistry()
    tools.register("generate_workout", generate_workout_tool)

    # 4) запускаємо executor
    executor = Executor(
        tools=tools,
        ask_user=ask_user_cli,
        observer=simple_observer,
    )
    executor.run_plan(plan)

    print("\n[FINAL CONTEXT]")
    from pprint import pprint
    pprint(executor.context)


if __name__ == "__main__":
    main()
