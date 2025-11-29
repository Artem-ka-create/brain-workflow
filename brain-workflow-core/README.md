🚀 Autonomous AI Agent - Архітектура і Документація
📋 Загальний Опис
Це autonomous AI agent система для хакатону, яка приймає high-level user goal, створює план виконання, і автономно виконує його використовуючи ReAct pattern (Reasoning + Acting).

🏗️ Архітектура Системи
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT                              │
│              "Create a learning plan for..."                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: PLANNER AGENT                                     │
│  - Аналізує user goal                                       │
│  - Створює 3-6 step план                                    │
│  - Визначає stages: question/analysis/action                │
│  - Output: Plan JSON                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: EVALUATOR                                         │
│  - Валідує план (completeness, clarity, executability)     │
│  - Може покращити план якщо є issues                       │
│  - Output: EvalResult (approved/improved plan)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: ORCHESTRATOR (Executor)                           │
│  - Виконує steps послідовно                                 │
│  - Керує memory (MemoryManager)                             │
│  - Передає контекст між steps                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
    ┌────────┐                  ┌────────┐
    │ Step 1 │    ...           │ Step N │
    └────┬───┘                  └────┬───┘
         │                           │
         ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│  REACT AGENT (для кожного action step)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ReAct Loop (max 10 iterations):                      │  │
│  │  1. THINK    → LLM reasoning про що робити далі       │  │
│  │  2. DECIDE   → вибрати tool або final answer          │  │
│  │  3. ACT      → виконати tool                          │  │
│  │  4. OBSERVE  → інтерпретувати результат               │  │
│  │  5. EVALUATE → чи достатньо для завершення?           │  │
│  │     ↓ YES → synthesize result                         │  │
│  │     ↓ NO  → повернутись до кроку 1                    │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  OBSERVER                                                   │
│  - Перевіряє чи досягнута глобальна ціль                   │
│  - Може зупинити execution достроково                      │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FINAL RESULTS                                              │
│  - Execution context з усіма результатами                   │
│  - Final output для користувача                             │
└─────────────────────────────────────────────────────────────┘

📁 Структура Файлів
project/
├── main.py                    # Головний entry point, orchestrator
├── .env                       # API keys (OPENAI_API_KEY)
├── requirements.txt           # Dependencies
└── agents/
    ├── __init__.py
    ├── planner.py            # Створює plan з user goal
    ├── evaluator.py          # Валідує і покращує plan
    ├── executor.py           # Виконує plan (Orchestrator + ReAct Agent)
    ├── memory.py             # Memory management з auto-summarization
    ├── observer.py           # Перевіряє global goal completion
    └── models.py             # Pydantic models (Plan, Step, EvalResult)

📄 Опис Файлів
1. main.py - Головний Orchestrator
Що робить:

Entry point програми
Об'єднує всі компоненти в один workflow
Реєструє tools (web_search, code_executor, file_write, data_analysis)
Виконує 4 фази: Planning → Evaluation → Execution → Results

Ключові компоненти:
pythonclass AutonomousAgent:
    def __init__(self):
        self.tools = setup_tools()  # Реєструє всі tools
    
    def run(self, user_goal: str):
        # PHASE 1: Planning
        plan = create_plan(user_goal)
        
        # PHASE 2: Evaluation
        eval_result = evaluate_plan(user_goal, plan)
        
        # PHASE 3: Execution
        executor = Executor(tools, ask_user, observer)
        executor.run_plan(plan)
        
        # PHASE 4: Display results
        return executor.context
Tools що реєструються:

web_search - пошук в інтернеті
code_executor - виконання коду
file_write - запис в файл
data_analysis - аналіз даних


2. agents/planner.py - Planner Agent
Що робить:

Приймає user goal (string)
Аналізує що треба зробити
Створює structured plan (3-6 steps)
Визначає для кожного step: stage, instruction, dependencies

Stages:

question - питання користувачу (якщо критично необхідно)
analysis - аналіз даних, обробка інформації
action - конкретна дія (search, generate, write file)

Output: Plan object з списком Step
Особливості:

Domain-agnostic (працює для будь-якої задачі)
Мінімізує questions (autonomous approach)
tool може бути null → ReAct agent сам вирішує який tool використати
Encoding fix для Unicode surrogates


3. agents/evaluator.py - Plan Evaluator
Що робить:

Перевіряє якість створеного плану
Оцінює за 7 критеріями:

Completeness - чи покриває всі кроки?
Clarity - чи чіткі інструкції?
Stages - чи правильно використані?
Step count - чи 3-6 steps?
Dependencies - чи правильні залежності?
Executability - чи може autonomous agent виконати?
Autonomy - чи мінімізовані питання користувачу?



Output: EvalResult з:

is_good: bool - чи план ОК
verdict: str - пояснення
confidence: float - впевненість 0-1
improved_plan: Plan | None - покращений план якщо треба


4. agents/executor.py - Orchestrator + ReAct Agent
Найважливіший файл! Містить 2 класи:
A. ReactAgent - Autonomous Executor
Що робить:

Виконує окремий step автономно
Використовує ReAct loop (max 10 iterations)
Сам вирішує які tools використати
Сам перевіряє коли готово

ReAct Loop (5 кроків):
pythonfor iteration in range(max_iterations):
    # 1. THINK (Reasoning)
    thought = self._reason(memory, iteration)
    # LLM аналізує: що зроблено? що треба далі?
    
    # 2. DECIDE ACTION
    action = self._decide_action(thought, memory)
    # LLM вибирає: use_tool або final_answer
    
    # 3. ACT (Execute)
    result = self._execute_action(action)
    # Виконує обраний tool
    
    # 4. OBSERVE
    observation = self._observe(result, step)
    # LLM інтерпретує результат
    
    # 5. EVALUATE
    is_complete = self._evaluate_completion(step, memory)
    # LLM перевіряє: чи достатньо для відповіді?
    
    if is_complete:
        return self._synthesize_final_result(memory)
Ключова особливість: Autonomous! Не просто викликає tool один раз, а думає → діє → оцінює → повторює до завершення.
B. Executor - Orchestrator
Що робить:

Керує виконанням всього плану
Викликає правильний метод для кожного stage:

_run_question_step() → питає користувача
_run_analysis_step() → LLM аналіз
_run_action_step() → ReAct Agent


Передає контекст між steps
Використовує MemoryManager для великих результатів
Викликає Observer після кожного step

Memory Integration:

Зберігає результати в MemoryManager
Автоматично створює summaries для великих outputs (>3000 chars)
Передає relevant context в ReAct Agent


5. agents/memory.py - Memory Management
2 класи:
A. MemoryManager
Що робить:

Зберігає execution context (результати всіх steps)
Автоматично створює summaries для великих результатів
Надає relevant context для кожного step (не весь context!)

Методи:
pythonmemory.store(key, value)
# → якщо value > 3000 chars, створює summary

memory.get(key)
# → повертає повний результат

memory.get_for_context(key)
# → повертає summary якщо є, інакше повний результат

memory.get_relevant_context(required_keys)
# → повертає тільки потрібні ключі (для ReAct Agent)

memory.get_context_stats()
# → статистика: keys, size, summarized_keys
Навіщо треба:

ReAct Agent отримує контекст з попередніх steps
Якщо контекст великий → LLM context overflow
Summary вирішує проблему: коротка версія замість повної

B. ConversationMemory (optional)
Що робить:

Зберігає історію розмови (chat history)
Для multi-turn dialogue (якщо треба follow-up)

Для хакатону: не критично, MemoryManager достатньо.

6. agents/observer.py - Goal Achievement Monitor
Що робить:

Перевіряє чи досягнута глобальна ціль
Викликається після кожного step
Може зупинити execution достроково

Поточна реалізація (simple):
pythondef simple_observer(plan, step_index, context):
    # Якщо останній step → stop
    if step_index == len(plan.steps) - 1:
        return True
    
    # Якщо є спеціальний ключ → stop
    if "final_workout_plan" in context:
        return True
    
    return False
Можна покращити:

LLM-based observer що аналізує чи goal achieved
Перевіряє quality результату
Вирішує чи треба ще steps


7. agents/models.py - Data Models
Pydantic models для type safety:
Step
pythonclass Step(BaseModel):
    id: str                        # "step_1"
    stage: "question|analysis|action"
    title: str                     # "Research requirements"
    instruction: str               # що робити
    depends_on: List[str]          # ["step_1", "step_2"]
    tool: Optional[str]            # "web_search" або null
    expected_input_keys: List[str] # які keys з context треба
    output_key: Optional[str]      # куди зберегти result
Plan
pythonclass Plan(BaseModel):
    goal: str                      # original user goal
    domain: str                    # "research", "coding", etc.
    steps: List[Step]              # 3-6 steps
    
    # Helper methods:
    def get_step_by_id(step_id) -> Step
    def get_dependencies_for_step(step_id) -> List[Step]
EvalResult
pythonclass EvalResult(BaseModel):
    is_good: bool                  # чи план OK
    verdict: str                   # пояснення
    improved_plan: Optional[Plan]  # покращений план
    confidence: float              # 0.0 - 1.0

🔄 Flow Execution (Приклад)
User Goal: "Research AI trends and create a report"
PHASE 1: Planning
json{
  "goal": "Research AI trends and create a report",
  "domain": "research",
  "steps": [
    {
      "id": "step_1",
      "stage": "action",
      "title": "Research AI trends",
      "instruction": "Search for latest AI trends in 2024",
      "tool": null,
      "output_key": "research_results"
    },
    {
      "id": "step_2",
      "stage": "analysis",
      "title": "Analyze trends",
      "instruction": "Categorize and summarize key trends",
      "expected_input_keys": ["research_results"],
      "output_key": "trend_summary"
    },
    {
      "id": "step_3",
      "stage": "action",
      "title": "Generate report",
      "instruction": "Create structured report document",
      "expected_input_keys": ["trend_summary"],
      "output_key": "final_report"
    }
  ]
}
```

### PHASE 2: Evaluation
```
Verdict: "Plan is well-structured with clear sequential steps..."
is_good: True
```

### PHASE 3: Execution

**Step 1 (action) → ReAct Agent:**
```
Iteration 1:
  💭 THINK: "Need to search for AI trends 2024"
  🔧 ACT: web_search("AI trends 2024")
  👁️ OBSERVE: "Found articles about LLMs, multimodal AI..."
  🔍 EVAL: NO - need more specific data

Iteration 2:
  💭 THINK: "Need more specific areas"
  🔧 ACT: web_search("computer vision breakthroughs 2024")
  👁️ OBSERVE: "Found CV advancements..."
  🔍 EVAL: YES - sufficient data ✅

Result → context["research_results"]
```

**Step 2 (analysis) → LLM Analysis:**
```
Analyzes research_results → creates structured summary
Result → context["trend_summary"]
```

**Step 3 (action) → ReAct Agent:**
```
Iteration 1:
  💭 THINK: "Need to format as report"
  🔧 ACT: file_write(filename="ai_trends_report.md", content=...)
  👁️ OBSERVE: "File written successfully"
  🔍 EVAL: YES ✅

Result → context["final_report"]
```

### PHASE 4: Results
```
Final output: "ai_trends_report.md created with comprehensive AI trends analysis"

🔑 Ключові Відмінності від Звичайного Chatbot
Звичайний ChatbotAutonomous AgentОдин LLM call → відповідьПлан → множина autonomous stepsНемає planningPlanner створює structured planНемає self-evaluationEvaluator перевіряє планПростий tool call (один раз)ReAct loop (thinking + retries)Немає memory між callsMemoryManager з auto-summarizationПотребує follow-up питаньAutonomous execution до завершення

🚀 Запуск
bash# 1. Install dependencies
pip install langchain langchain-openai python-dotenv pydantic

# 2. Set up .env
echo "OPENAI_API_KEY=your_key" > .env

# 3. Run
python main.py
```

**Input:**
```
Enter your goal: Research Python best practices and create a guide
```

**Output:**
```
✅ Tools registered: ['web_search', 'code_executor', ...]
🧠 MemoryManager enabled

🎯 PHASE 1: PLANNING
✅ Plan created with 4 steps

🔍 PHASE 2: EVALUATION
✅ Plan approved

⚙️ PHASE 3: EXECUTION
[STEP 1/4] Research Python practices (action)
  🤖 ReAct Agent executing...
  💭 THOUGHT: Need to search...
  ...
✅ Step completed

📊 PHASE 4: RESULTS
🎯 FINAL RESULT: [guide content]

💡 Що Робить Систему "Autonomous"

Planning - сам розбиває goal на steps
Self-evaluation - перевіряє чи plan логічний
ReAct Loop - думає → діє → оцінює → повторює
Tool Selection - сам вибирає які tools використати
Completion Detection - сам знає коли готово
Error Recovery - якщо tool fails, пробує інакше
Memory Management - керує контекстом автоматично


📊 Dependencies
txtlangchain
langchain-openai
python-dotenv
pydantic
openai