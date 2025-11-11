# SQL Agent - AI-Powered Data Assistant

An intelligent SQL assistant that uses natural language processing and plan-based execution to help non-technical users query databases and create visualizations through conversational interactions.

> 📄 **For detailed project overview and objectives, see [Project Proposal.pdf](Project%20Proposal.pdf)**

## 🌟 Features

### Core Capabilities
- **Natural Language Queries**: Ask questions in plain English, get SQL results
- **Plan-Based Execution**: Complex questions automatically decomposed into logical steps
- **Multi-Step Reasoning**: Context flows between steps for sophisticated analysis
- **Smart Visualizations**: Automatic chart generation (bar, line, pie, scatter)
- **Conversational Memory**: Maintains context across multiple turns
- **Real-Time Feedback**: See the plan and execution progress as it happens
- **Error Recovery**: Automatic retry with intelligent error correction (up to 10 attempts per step)

### Security & Safety
- **Read-Only Operations**: Only SELECT queries allowed
- **Query Sanitization**: Dangerous keywords automatically blocked
- **Automatic Limiting**: Row limits enforced to prevent excessive data retrieval
- **Column Validation**: Prevents LLM hallucinations in chart generation

## 🏗️ Architecture

### Plan-Execute-Synthesize Pattern

```
User Question
    ↓
Planner (LLM creates numbered step plan)
    ↓
Execute Step Loop (with context from previous steps)
    ↓
Generate Final Answer (synthesize from all results)
    ↓
Update Chat History
```

### Technology Stack
- **Package Manager**: uv for fast, reliable dependency management
- **Orchestration**: LangGraph for state machine workflow
- **LLM**: OpenAI GPT-4o-mini for planning, SQL generation, and synthesis
- **SQL Execution**: pandasql on pandas DataFrames
- **Visualization**: matplotlib + seaborn
- **UI**: Gradio chat interface with streaming
- **Data**: Excel files via openpyxl

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key

### Installation

1. **Install uv** (if not already installed):
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Clone the repository**:
```bash
git clone <repository-url>
cd SQL-Agent
```

3. **Install dependencies with uv**:
```bash
uv sync
```

4. **Set up environment variables**:
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY="your-api-key-here"
```

5. **Prepare your data**:
Place your Excel file in the `data_sample/` directory (default: `Accrual_Accounts.xlsx`)

6. **Run the application**:
```bash
uv run python main.py
```

The Gradio UI will launch at `http://localhost:7860`

### Alternative: Using pip

If you prefer using pip instead of uv:
```bash
pip install -e .
python main.py
```

## 📊 Usage Examples

### Simple Query
```
User: "What is the highest transaction value?"
Agent: Creates 1-step plan → Executes → Returns answer
```

### Complex Multi-Step Query
```
User: "Find the top 3 merchants by sales and show their monthly breakdown"
Agent: 
  Step 1: Find top 3 merchants by total sales
  Step 2: Get monthly sales for those merchants
  Synthesizes comprehensive answer from both results
```

### Visualization Request
```
User: "Chart the quarterly revenue for categories above $10k"
Agent:
  Step 1: Find categories with revenue > $10k
  Step 2: Calculate quarterly revenue for those categories
  Step 3: Create visualization and synthesize answer
```

### Follow-Up Questions
```
User: "What were the sales in Q1 2023?"
Agent: [Provides answer]

User: "How does that compare to Q2?"
Agent: [Uses conversation history for context]
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
LLM_MODEL = "gpt-4o-mini"           # OpenAI model
MAX_RETRIES = 10                     # Retry attempts per step
MAX_ROWS = 100                       # Row limit for queries
MAX_CONVERSATION_HISTORY = 5         # Messages to keep in context
CHART_OUTPUT_PATH = "charts"         # Directory for generated charts
```

## 📁 Project Structure

```
SQL-Agent/
├── src/
│   ├── agent/
│   │   ├── graph.py              # LangGraph workflow & nodes
│   │   └── agent_prompts.py      # LLM prompts
│   ├── tools/
│   │   ├── sql_tool.py           # SQL execution & sanitization
│   │   ├── visualization_tool.py # Chart generation
│   │   └── tools_prompts.py      # Tool-specific prompts
│   ├── data/
│   │   └── handler.py            # Data loading & schema generation
│   └── ui/
│       └── app.py                # Gradio interface
├── data_sample/                  # Sample data files
├── charts/                       # Generated visualizations
├── config.py                     # Configuration
├── main.py                       # Entry point
├── pyproject.toml               # Project metadata & dependencies
├── uv.lock                      # Locked dependencies (uv)
└── .env.example                 # Environment variables template
```

## 🎯 How It Works

### 1. Planning Phase
The planner node analyzes your question and creates a numbered list of steps:
- Simple questions → 1-step plan
- Complex questions → Multi-step plan with logical sequence
- Visualization requests → Data steps + chart step

### 2. Execution Phase
Each step is executed sequentially:
- LLM generates SQL query for the step instruction
- Previous step results are available as context
- Query is executed with automatic sanitization
- Results stored as markdown for next step
- Inline retry (up to 10 attempts) if errors occur

### 3. Synthesis Phase
Final answer is generated by:
- Reviewing the entire plan
- Analyzing all step results
- Creating visualization if requested
- Synthesizing comprehensive natural language answer

## 🛡️ Security Features

### Query Sanitization
- **Keyword Blocking**: DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE
- **SELECT Enforcement**: Only SELECT statements allowed
- **Automatic LIMIT**: Adds LIMIT clause if missing
- **Read-Only Execution**: Uses pandasql on DataFrames (no direct DB writes)

### LLM Safety
- **Column Validation**: Checks if LLM-selected columns exist
- **Structured Outputs**: Pydantic models ensure type safety
- **Error Context**: Failed queries include error messages for correction

## 🧪 Development

### Setting Up Development Environment

```bash
# Install with dev dependencies
uv sync --extra dev

# Or install dev dependencies separately
uv pip install -e ".[dev]"
```

### Code Quality Tools

**Linting**:
```bash
uv run ruff check .
```

**Formatting**:
```bash
uv run black .
```

**Auto-fix**:
```bash
uv run ruff check . --fix
```

**Run all checks**:
```bash
uv run ruff check . --fix && uv run black .
```

### Pre-commit Hooks
```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## 📈 Performance Considerations

### Token Usage
- Multiple LLM calls per question (planning + steps + synthesis)
- Consider costs for complex multi-step queries
- Use conversation history limit to control context size

### Execution Time
- Sequential step execution (not parallel)
- Time increases with plan complexity
- Retry attempts can extend duration

### Optimization Tips
- Use efficient model (gpt-4o-mini)
- Limit conversation history (5 messages)
- Restrict row counts (100 rows)
- Cache results when possible

##  Contact

[andrej.cicmansky@gmail.com](mailto:andrej.cicmansky@gmail.com)

## 🙏 Acknowledgments

Built with:
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - State machine orchestration
- [Gradio](https://gradio.app/) - UI framework
- [OpenAI](https://openai.com/) - GPT-4o-mini model

## 🎓 Example Session

```
User: "What's the total transaction value by year?"

Agent: I've created a plan:
  - Find total transaction value grouped by year
  
Executing Step 1... Done.

Agent: Based on the data, here are the total transaction values by year:
- 2021: $1,234,567.89
- 2022: $2,345,678.90
- 2023: $3,456,789.01

---

User: "Can you chart that?"

Agent: I've created a plan:
  - Use the previous year totals
  - Create a bar chart showing transaction values by year
  
Executing Step 1... Done.
Executing Step 2... Done.

Agent: [Shows bar chart]
I've created a bar chart showing the transaction values by year. 
As you can see, there's a clear upward trend with each year 
showing significant growth over the previous year.
```

## 🚦 Status

**Current Version**: 0.1.0 (Alpha)  
**Status**: ✅ Fully functional for development/demo  
**Production Ready**: ❌ Not yet

---