# agents/evaluator.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .models import Plan, EvalResult
from dotenv import load_dotenv

load_dotenv()


llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)


evaluator_prompt = ChatPromptTemplate.from_template(
    """
You are a strict evaluator of workout plans for an autonomous agent.

User goal:
{goal}

Current plan (JSON):
{plan_json}

Check:
- Is the plan focused on workouts only?
- Are stages correctly used (question / analysis / action)?
- Is the number of steps reasonable (3–8)?
- Can an executor run steps sequentially without ambiguity?

If the plan is not good, construct a NEW improved Plan JSON that fixes the issues.
If the plan is good, you may just reuse the current plan.

Answer strictly using the EvalResult schema.
"""
)


def evaluate_plan(goal: str, plan: Plan) -> EvalResult:
    chain = evaluator_prompt | llm.with_structured_output(EvalResult)

    return chain.invoke(
    {
        "goal": goal,
        "plan_json": plan.json(indent=2),
    }
)
