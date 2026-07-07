# Architecture Terms

This document defines the four core architecture concepts demonstrated by this project, and explains why this is not just a scripted pipeline.

## Harness

The runtime environment around the model (agent). It connects the model to tools, memory, shell, files, approvals, and messaging.

In this project, the harness is minimal: the Python CLI (`resume_loop.py`) plus the adapter (`llm_adapter.py`) and tool dispatcher (`tools.py`).

The harness is not the model. The harness is the system that lets the model act safely and usefully.

## Agent

The decision-making component that receives context, chooses the next action, and works toward the goal.

In this project:
- `MockAdapter` is the agent backend (this is the mock-only version).
- The agent receives messages, available tools, and prior observations.
- The agent returns either a tool request, a user-clarification request, or a final resume.

The agent is not the whole application. It is the decision-making component inside the harness.

## Agentic Loop

The repeated execution cycle:

1. Receive goal/context
2. Decide next action
3. Call a tool
4. Observe result
5. Decide again
6. Stop when complete

In this project, `resume_loop.py` implements this loop visibly. Each iteration logs:
- iteration number
- agent decision
- selected tool, if any
- tool result / observation
- whether the loop continues or stops

This mock version uses a deterministic adapter for reliability, but it still passes through the same loop and tool-dispatch path.

## Skill

A portable instruction file (`SKILL.md`) that tells an agent platform how to operate this project. It defines when to use the tool, how to initialize it, how to run it, the evidence rules, the constraints, and the verification checklist.

## State

Persistent local memory. Here, SQLite stores user profile, experience entries, bullets, tool inventory, certifications, answers, and run records.

## Stopping Condition

The loop stops when:
- a grounded Markdown resume is produced
- the loop reaches the maximum iteration limit (8)
- the agent signals that user input is needed and cannot be inferred

## Why This Is Not Just a Scripted Pipeline

A scripted pipeline runs fixed steps in order. The output of each step feeds the next, but there is no decision point. Step 3 always follows Step 2.

This mock version simulates the agent choosing tools based on current observations. After querying the experience database, the agent might decide to ask the user a question, or it might decide it has enough evidence and generate the resume immediately. The decision depends on what the tools returned, not a predetermined sequence.

This mock version uses a deterministic adapter for demo reliability, but it still passes through the same tool interface so the loop remains visible and testable. The architecture is the point: the loop, not the script.
