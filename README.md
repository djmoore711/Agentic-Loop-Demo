# Resume Agentic Loop — Mock Demo

A self-contained Python CLI that demonstrates the **agentic loop pattern** using resume tailoring as the example domain.

This is a **mock/demo project**. It uses a deterministic offline adapter that simulates the agent deciding which tool to call next. No API keys, no LLM calls, no external services required.

## What it demonstrates

- **Agent** — a decision-making component (`MockAdapter`) that receives context and chooses the next action
- **Agentic loop** — the repeated decide → tool → observe → decide cycle in `resume_loop.py`
- **Harness** — the runtime that connects the agent to tools, database, and CLI
- **Tool interface** — the agent can query experience, search bullets, ask questions, and generate output through defined tools

## What it does NOT claim

This is not a production resume builder. The mock adapter follows a predictable scripted sequence — it doesn't call a real LLM. The value is in the architecture: the loop structure, the tool dispatch, the state management, and the separation between the agent and the harness.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize the database and seed sample data
python resume_loop.py init
python resume_loop.py seed

# Run the demo with a sample job description
python resume_loop.py start --file sample_data/sample_job_description.txt
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
python resume_loop.py start --file <path>          # Read from a file
python resume_loop.py start --url <url>            # Fetch from URL
python resume_loop.py start --text "<raw text>"    # Pass inline text
python resume_loop.py start --file <path> --interactive  # Enable user prompts
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
resume_loop.py          CLI entry point and agentic loop
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
python resume_loop.py init
python resume_loop.py seed
python resume_loop.py db-summary
```

Expected after seed: 1 profile, 3 experience entries, 5 bullets, 7 tools, 2 certs.

## Known limitations

- Mock adapter follows a fixed sequence — it simulates rather than truly deciding
- User answers in interactive mode are stored but not yet used in resume generation
- URL extraction may fail on JavaScript-rendered pages
- No tests are currently included
