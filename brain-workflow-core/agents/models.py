# agents/models.py (IMPROVED VERSION)
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
        description="Name of tool to use for action stage (if applicable). Can be null - ReAct agent will decide autonomously."
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
    goal: str = Field(..., description="The original user goal")
    domain: str = Field(
        default="general",
        description="Domain of the task (auto-detected): research, coding, planning, analysis, creative, etc."
    )
    steps: List[Step] = Field(
        ...,
        description="Sequence of steps to achieve the goal"
    )

    def get_step_by_id(self, step_id: str) -> Optional[Step]:
        """Helper method to get step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_dependencies_for_step(self, step_id: str) -> List[Step]:
        """Get all dependency steps for a given step"""
        step = self.get_step_by_id(step_id)
        if not step:
            return []

        return [self.get_step_by_id(dep_id) for dep_id in step.depends_on
                if self.get_step_by_id(dep_id) is not None]


class EvalResult(BaseModel):
    is_good: bool = Field(..., description="Whether the plan is good enough to execute")
    verdict: str = Field(..., description="Explanation of the evaluation decision")
    improved_plan: Optional[Plan] = Field(
        default=None,
        description="If plan is not good, this contains the improved version"
    )
    confidence: float = Field(
        default=0.5,
        description="Confidence score 0-1 of the evaluation",
        ge=0.0,
        le=1.0
    )