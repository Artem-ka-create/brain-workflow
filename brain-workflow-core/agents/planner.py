# agents/planner.py (IMPROVED VERSION)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

from .models import Plan, Step

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

planner_prompt = ChatPromptTemplate.from_template(
    """
You are an autonomous planning agent that breaks down high-level user goals into executable steps.

User goal:
{goal}

Available tools for execution:
{tools_list}

Your task:
1. Analyze the user's goal and determine what needs to be done
2. Break it down into 3-6 clear, sequential steps
3. Each step must have a stage:
   - "question": Ask user for critical missing information (only if absolutely necessary)
   - "analysis": Analyze gathered data, make decisions, or process information
   - "action": Execute a concrete action (search, generate, compute, write file, etc.)

Rules:
- Keep steps atomic: each should produce ONE clear output
- Use tools when appropriate (web_search for research, file_write for documents, code_executor for computations)
- Set 'tool' to null if the step doesn't need a specific tool (ReAct agent will decide)
- Minimize questions to user - only ask for info that's absolutely critical and not inferrable
- Steps should be sequential and have clear dependencies
- Number of steps: 3-6 (no more, no less)

IMPORTANT: 
- The 'tool' field can be null - the ReAct agent will autonomously decide which tools to use
- Only specify 'tool' if you want to force a specific tool for that step
- expected_input_keys should list context keys from previous steps that this step needs

Return valid JSON matching the Plan schema.
Do not include any extra text, markdown formatting, or explanations - ONLY the JSON.
"""
)


def create_plan(goal: str, available_tools: list = None) -> Plan:
    """
    Створює план виконання для заданої цілі

    Args:
        goal: Ціль користувача
        available_tools: Список доступних tools (optional)

    Returns:
        Plan object
    """

    # Fix encoding issues - remove surrogates and clean string
    goal = goal.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    goal = ''.join(char for char in goal if ord(char) < 0x10000)  # Remove surrogates

    # Default tools якщо не передано
    if available_tools is None:
        available_tools = [
            "web_search - Search the web for information",
            "code_executor - Execute code (Python, JS, etc.)",
            "file_write - Write content to a file",
            "data_analysis - Analyze structured data"
        ]

    tools_description = "\n".join([f"  - {tool}" for tool in available_tools])

    chain = planner_prompt | llm.with_structured_output(Plan)

    result = chain.invoke({
        "goal": goal,
        "tools_list": tools_description
    })

    return result