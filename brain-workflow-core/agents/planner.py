# agents/planner.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

from .models import Plan, Step

llm = ChatOpenAI(model="gpt-5-mini", temperature=0)


planner_prompt = ChatPromptTemplate.from_template(
    """
You are a planning agent focused ONLY on workout (training) plans.

User goal:
{goal}

Rules:
- Focus exclusively on workouts: training structure, frequency, volume, exercises.
- Do NOT include nutrition, supplements, sleep, mindset unless the goal explicitly demands it.
- Break the work into a small, clear sequence of steps.
- Each step must be tagged with a stage:
  - "question": ask the user for missing info (only if really necessary).
  - "analysis": analyze user's info and constraints to prepare an action.
  - "action": produce concrete workout artifacts (e.g. weekly schedule, exercise list).
- Prefer to keep the number of steps from 3 to 8.
- Use 'tool' only for steps that will call an external function, otherwise null.

Return a valid JSON matching the Plan schema.
Do not include any extra text, only JSON.
"""
)


def create_plan(goal: str) -> Plan:
    chain = planner_prompt | llm.with_structured_output(Plan)
    return chain.invoke({"goal": goal})
