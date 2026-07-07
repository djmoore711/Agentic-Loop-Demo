#!/usr/bin/env python3
"""
Resume Agentic Loop - Main Entry Point

This file contains:
  1. CLI command parsing (the Harness entry point)
  2. The agentic loop (run_loop) - the model-driven decision cycle
  3. Command dispatch for all CLI subcommands

Architecture concepts demonstrated:
  - Agent: the LLM adapter (MockAdapter, mock-only)
  - Agentic loop: run_loop() - model decides which tool to call next
  - Harness: this file + database.py + tools.py + config loading
"""

from __future__ import annotations

import json
import os
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from analyzer import analyze
from dotenv import load_dotenv
from extractor import extract
from generator import generate
from llm_adapter import get_adapter
from models import JobDescription, ToolCall
from prompts import SYSTEM_PROMPT
import database
from tools import TOOL_DEFINITIONS, ask_user, execute_tool, tool_result_to_json

load_dotenv()

console = Console()

MAX_ITERATIONS = 8


# ---------------------------------------------------------------------------
# THE AGENTIC LOOP
# ---------------------------------------------------------------------------


def run_loop(jd: JobDescription, interactive: bool = False) -> str:
    """The model-driven agentic loop.

    This is where the agent (model or mock) chooses tools.
    This is where tool results are fed back.
    This is where the loop stops.

    Flow:
      1. Agent receives the goal (job description) and available tools
      2. Agent decides: call a tool, ask the user, or produce final output
      3. If tool call: execute the tool, feed result back, continue
      4. If user input needed: ask, store answer, continue
      5. If final resume: save and return
      6. Stop after MAX_ITERATIONS
    """
    adapter = get_adapter()

    # Set interactive flag for ask_user tool
    ask_user._interactive = interactive

    # Create a run record
    run_id = database.create_run(
        job_title=jd.title or "Unknown",
        company=jd.company or "Unknown",
        source_url=jd.source_url or "",
        raw_job_description=jd.raw_text,
    )

    # Step 1: Analyze requirements (harness pre-processing)
    with Progress(SpinnerColumn(), TextColumn("[bold blue]Analyzing job description..."), transient=True) as progress:
        progress.add_task("analyze", total=1)
        requirements = analyze(jd, mock=True)

    database.update_run(run_id, extracted_requirements=json.dumps(requirements, default=str))

    console.print()
    console.print(Panel.fit(
        f"[bold]Agentic Loop Starting[/bold]\n"
        f"Mode: mock\n"
        f"Job: {requirements.get('title', jd.title or 'Unknown')}\n"
        f"Company: {requirements.get('company', jd.company or 'Unknown')}\n"
        f"Max iterations: {MAX_ITERATIONS}",
        title="[bold cyan]Harness[/bold cyan]",
        border_style="cyan",
    ))

    # Build initial messages
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Create a tailored resume for this job:\n\n"
                       f"Title: {requirements.get('title', jd.title or 'Unknown')}\n"
                       f"Company: {requirements.get('company', jd.company or 'Unknown')}\n\n"
                       f"Requirements:\n{json.dumps(requirements, indent=2, default=str)}",
        },
    ]

    matched_experience: list[dict[str, Any]] = []
    user_answers: list[dict[str, str]] = []
    final_resume: str = ""

    for iteration in range(MAX_ITERATIONS):
        console.print(f"\n[bold yellow]--- Iteration {iteration + 1}/{MAX_ITERATIONS} ---[/bold yellow]")

        # AGENT DECIDES
        response = adapter.complete(messages, tools=TOOL_DEFINITIONS)

        if response.tool_calls:
            # TOOL CALL(s)
            for tc in response.tool_calls:
                console.print(f"  [bold green]Agent decision:[/bold green] call tool [bold]{tc.name}[/bold]")
                console.print(f"  [dim]Arguments:[/dim] {json.dumps(tc.arguments, indent=2)}")

                result = execute_tool(tc)

                # Track matched experience for final generation
                if tc.name == "query_experience" and result.success:
                    matched_experience = result.result.get("entries", [])

                # Track user answers
                if tc.name == "ask_user" and result.success:
                    user_answers.append(result.result)

                console.print(f"  [bold blue]Observation:[/bold blue] {tool_result_to_json(result)[:200]}...")
                messages.append({
                    "role": "tool",
                    "name": tc.name,
                    "content": tool_result_to_json(result),
                })
            continue

        if response.stop_reason == "needs_user_input":
            # USER CLARIFICATION
            console.print("  [bold green]Agent decision:[/bold green] ask user for clarification")
            for q in response.questions:
                console.print(f"  [magenta]Question:[/magenta] {q.get('question', '?')}")
                if interactive:
                    answer = input("  > ").strip()
                    database.store_answer(
                        jd.title or "Unknown",
                        jd.company or "Unknown",
                        q.get("question", ""),
                        answer,
                    )
                    user_answers.append({"question": q.get("question", ""), "answer": answer})
                else:
                    console.print("  [dim](non-interactive: using fallback answer)[/dim]")
                    database.store_answer(
                        jd.title or "Unknown",
                        jd.company or "Unknown",
                        q.get("question", ""),
                        "[non-interactive fallback]",
                    )
                    user_answers.append({"question": q.get("question", ""), "answer": "[fallback]"})

            messages.append({
                "role": "user",
                "content": json.dumps(user_answers, default=str),
            })
            continue

        if response.stop_reason == "final_resume":
            # STOPPING CONDITION
            console.print("  [bold green]Agent decision:[/bold green] produce final resume")
            console.print("  [bold red]Stopping condition met:[/bold red] final resume produced")

            # Mock version: always generate from DB state
            final_resume = generate(
                jd=jd,
                requirements=requirements,
                matched_experience=matched_experience or database.query_experience("security"),
                adapter=adapter,
                mock=True,
            )

            break

        # end_turn without final resume: check if we have enough to generate
        if response.stop_reason == "end_turn" and not final_resume:
            console.print("  [dim]Agent returned end_turn. Generating from available evidence...[/dim]")
            final_resume = generate(
                jd=jd,
                requirements=requirements,
                matched_experience=matched_experience or database.query_experience("security"),
                adapter=adapter,
                mock=True,
            )
            break

    else:
        # Loop exhausted
        console.print(f"\n[bold red]Loop exhausted after {MAX_ITERATIONS} iterations.[/bold red]")
        console.print("[yellow]Producing best-effort resume from gathered evidence...[/yellow]")
        final_resume = generate(
            jd=jd,
            requirements=requirements,
            matched_experience=matched_experience or database.query_experience("security"),
            adapter=adapter,
            mock=True,
            )

    # Save output
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "resume.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_resume)

    database.update_run(run_id, generated_resume=final_resume, status="complete")

    console.print(f"\n[bold green]Resume saved to:[/bold green] {output_path}")
    return final_resume


# ---------------------------------------------------------------------------
# CLI COMMAND DISPATCH (The Harness entry point)
# ---------------------------------------------------------------------------


def cmd_init(args):
    """Initialize the SQLite database."""
    database.init_db()
    console.print("[bold green]Database initialized.[/bold green]")
    console.print(f"  Database file: {database.DB_PATH}")


def cmd_seed(args):
    """Seed fictional sample data."""
    msg = database.seed_sample_data()
    console.print(f"[bold green]{msg}[/bold green]")


def cmd_db_summary(args):
    """Print database table counts."""
    summary = database.get_db_summary()
    table = Table(title="Database Summary")
    table.add_column("Table", style="cyan")
    table.add_column("Rows", style="magenta", justify="right")
    for table_name, count in summary.items():
        table.add_row(table_name, str(count))
    console.print(table)


def cmd_start(args):
    """Start the agentic loop on a job description."""
    jd = extract(file_path=args.file, url=args.url, text=args.text)
    interactive = args.interactive
    console.print(f"[bold]Mode:[/bold] mock")
    console.print(f"[bold]Interactive:[/bold] {interactive}")
    console.print(f"[bold]Extraction method:[/bold] {jd.extraction_method}")
    console.print(f"[bold]Text length:[/bold] {len(jd.raw_text)} chars")
    run_loop(jd, interactive=interactive)


def cmd_export(args):
    """Export the most recent resume to a specified path."""
    run = database.get_latest_run()
    if not run or not run.get("generated_resume"):
        # Try output/resume.md directly
        output_path = os.path.join(os.path.dirname(__file__), "output", "resume.md")
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            console.print("[bold red]No resume found. Run 'start' first.[/bold red]")
            return
    else:
        content = run["generated_resume"]

    export_path = args.output or os.path.join(os.path.dirname(__file__), "output", "exported_resume.md")
    os.makedirs(os.path.dirname(export_path), exist_ok=True) if os.path.dirname(export_path) else None
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(content)
    console.print(f"[bold green]Resume exported to:[/bold green] {export_path}")


def cmd_interactive(args):
    """Interactive mode: paste a job description."""
    console.print("[bold]Interactive Mode[/bold]")
    console.print("Paste the job description. Press Ctrl+D (or Ctrl+Z on Windows) when done.\n")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    text = "\n".join(lines).strip()
    if not text:
        console.print("[bold red]No input received.[/bold red]")
        return
    jd = extract(text=text)
    run_loop(jd, interactive=True)


def main():
    """CLI entry point - the harness."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Resume Agentic Loop - a model-driven agentic loop demo",
        prog="resume_loop",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    subparsers.add_parser("init", help="Initialize the SQLite database")

    # seed
    subparsers.add_parser("seed", help="Seed fictional sample data")

    # db-summary
    subparsers.add_parser("db-summary", help="Print database table counts")

    # start
    start_parser = subparsers.add_parser("start", help="Start the agentic loop on a job description")
    start_group = start_parser.add_mutually_exclusive_group(required=True)
    start_group.add_argument("--file", help="Path to a job description file")
    start_group.add_argument("--url", help="URL of a job posting")
    start_group.add_argument("--text", help="Raw job description text")
    start_parser.add_argument("--interactive", action="store_true", help="Enable interactive user prompts")

    # export
    export_parser = subparsers.add_parser("export", help="Export the most recent resume")
    export_parser.add_argument("--output", help="Output file path")

    # interactive
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode - paste a job description")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "seed":
        cmd_seed(args)
    elif args.command == "db-summary":
        cmd_db_summary(args)
    elif args.command == "start":
        cmd_start(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "interactive":
        cmd_interactive(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
