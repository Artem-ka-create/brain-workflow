# agents/models.py
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


Stage = Literal["question", "analysis", "action"]


class Step(BaseModel):
    id: str = Field(..., description="Unique step id, e.g. 'step_1'")
    stage: Stage = Field(..., description="Stage type: question | analysis | action")
    title: str = Field(..., description="Short human-readable name of the step")
    instruction: str = Field(..., description="What exactly the agent/tool should do")
    depends_on: List[str] = Field(
        default_factory=list,
        description="Ids of steps that must be completed before this one"
    )
    tool: Optional[str] = Field(
        default=None,
        description="Name of tool to use for action stage (if applicable)"
    )
    expected_input_keys: List[str] = Field(
        default_factory=list,
        description="Which keys from context/user data are required for this step"
    )
    output_key: Optional[str] = Field(
        default=None,
        description="Under which key to store the result in context/memory"
    )


class Plan(BaseModel):
    goal: str
    domain: str = "workout_planning"
    steps: List[Step]


class EvalResult(BaseModel):
    is_good: bool
    verdict: str
    improved_plan: Optional[Plan] = None
