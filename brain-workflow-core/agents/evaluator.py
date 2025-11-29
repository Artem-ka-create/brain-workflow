# agents/evaluator.py (IMPROVED VERSION)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .models import Plan, EvalResult
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

evaluator_prompt = ChatPromptTemplate.from_template(
    """
You are a strict evaluator of execution plans for an autonomous AI agent system.

User goal:
{goal}

Current plan (JSON):
{plan_json}

Evaluate this plan based on the following criteria:

1. COMPLETENESS: Does the plan cover all necessary steps to achieve the goal?
2. CLARITY: Are step instructions clear and actionable?
3. STAGES: Are stages used correctly?
   - "question": only for critical user input
   - "analysis": for data processing, decision making
   - "action": for concrete actions (search, generate, write, execute)
4. STEP COUNT: Is the number of steps reasonable (3-6 steps)?
5. DEPENDENCIES: Are step dependencies correctly specified?
6. EXECUTABILITY: Can an autonomous agent execute these steps sequentially?
7. AUTONOMY: Does the plan minimize user interaction (questions)?

Common issues to check:
- Too many question steps (should be 0-1, max 2)
- Steps that are too vague or broad
- Missing dependencies between steps
- Too many or too few steps
- Steps that can't be executed autonomously

If the plan has significant issues:
- Construct a NEW improved Plan JSON that fixes the problems
- Maintain the original goal but restructure the steps

If the plan is acceptable:
- Set is_good = true
- You can still provide improved_plan if you have minor suggestions

Respond using the EvalResult schema with:
- is_good: boolean
- verdict: detailed explanation (2-4 sentences)
- confidence: 0.0 to 1.0
- improved_plan: new Plan object if needed (otherwise null)
"""
)


def evaluate_plan(goal: str, plan: Plan) -> EvalResult:
    """
    Оцінює якість плану і повертає вердикт

    Args:
        goal: Оригінальна ціль користувача
        plan: План для оцінки

    Returns:
        EvalResult з вердиктом і можливо покращеним планом
    """
    chain = evaluator_prompt | llm.with_structured_output(EvalResult)

    result = chain.invoke({
        "goal": goal,
        "plan_json": plan.model_dump_json(indent=2),
    })

    return result