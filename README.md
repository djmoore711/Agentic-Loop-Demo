# Agentic Loop Demo

A Python CLI that demonstrates the **decide → tool → observe → repeat** pattern. The agent receives a goal, inspects available tools and data, calls them, observes results, and decides what to do next — all without a real LLM.

This is a mock. No API keys, no model calls, no dependencies beyond `pip install`. It exists to make the agentic loop visible in under 30 seconds.

## What it demonstrates

- **Agent** — a decision-making component (`MockAdapter`) that receives context and chooses the next action
- **Agentic loop** — the repeated decide → tool → observe → decide cycle in `main.py`
- **Harness** — the runtime that connects the agent to tools, database, and CLI
- **Tool interface** — the agent can query experience, search bullets, ask questions, and generate output through defined tools

## What it does NOT claim

This is not a production resume builder. The mock adapter follows a predictable scripted sequence — it doesn't call a real LLM. The value is in the architecture: the loop structure, the tool dispatch, the state management, and the separation between the agent and the harness.

## Quick start

```bash
# Download the project
git clone https://github.com/djmoore711/Agentic-Loop-Demo.git
cd Agentic-Loop-Demo

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database and seed sample data
python main.py init
python main.py seed

# Run the demo with a sample job description
python main.py start --file sample_data/sample_job_description.txt
```

## Run tests

```bash
source .venv/bin/activate
python -m pytest
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Create the SQLite database schema |
| `seed` | Load fictional sample data (profile, experience, bullets, tools) |
| `db-summary` | Print table row counts |
| `start` | Run the agentic loop on a job description |
| `export` | Export the most recent resume |
| `interactive` | Paste a job description and run interactively |

### `start` options

```
python main.py start --file <path>          # Read from a file
python main.py start --url <url>            # Fetch from URL
python main.py start --text "<raw text>"    # Pass inline text
python main.py start --file <path> --interactive  # Enable user prompts
```

## Example output

After running `init` → `seed` → `start --file sample_data/sample_job_description.txt`:

```
╭──────────────────────────────────────────────────╮
│                    Harness                        │
│  Agentic Loop Starting                            │
│  Mode: mock                                       │
│  Job: Senior Security Automation Engineer         │
│  Company: Nexus Dynamics                          │
│  Max iterations: 8                                │
╰──────────────────────────────────────────────────╯

--- Iteration 1/8 ---
  Agent decision: call tool query_tools
  Observation: {"count": 1, "tools": [{"tool_name": "Python", ...}]}...

--- Iteration 2/8 ---
  Agent decision: call tool query_experience
  Observation: {"count": 2, "entries": [...]}...

--- Iteration 6/8 ---
  Agent decision: produce final resume
Resume saved to: ./output/resume.md
```

The generated resume is saved to `output/resume.md`.

## Project structure

```
main.py          CLI entry point and agentic loop
llm_adapter.py          Mock adapter (the "Agent")
models.py               Data models
tools.py                Tool functions and dispatch
database.py             SQLite state manager
analyzer.py             Job description analysis
generator.py            Resume generation from evidence
prompts.py              Prompt templates
extractor.py            URL/file/text extraction
templates/              Markdown resume template
sample_data/            Sample job description and profile
```

## Test it works

```bash
python main.py init
python main.py seed
python main.py db-summary
```

Expected after seed: 1 profile, 3 experience entries, 5 bullets, 7 tools, 2 certs.

## Known limitations

- Mock adapter follows a fixed sequence — it simulates rather than truly deciding
- User answers in interactive mode are stored but not yet used in resume generation
- URL extraction may fail on JavaScript-rendered pages
