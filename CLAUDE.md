# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nanocode** is the companion codebase for the book "Build Your Own Coding Agent." It's a terminal-based AI coding agent built from scratch in pure Python — no frameworks, no LangChain, just `requests`, `subprocess`, and `python-dotenv`. The codebase grows chapter-by-chapter from a 47-line REPL skeleton (ch01) to a 767-line feature-complete agent (ch11/ch12).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add ANTHROPIC_API_KEY (and optionally DEEPSEEK_API_KEY) to .env
```

## Commands

```bash
# Run the full agent (plan/read-only mode by default)
python ch11/nanocode.py

# Run with write/execute enabled
python ch11/nanocode.py --act

# Run with local Ollama model
NANOCODE_BRAIN=ollama python ch11/nanocode.py

# Run tests (no API key required — uses FakeBrain)
cd ch09 && pytest

# Run a single test
cd ch09 && pytest test_nanocode.py::test_name -v
```

In-agent commands: `/q` (quit), `/switch` (toggle LLM provider), `/mode [plan|act]`

## Architecture

The project uses a progressive learning model — each `ch01/` through `ch12/` directory is a complete, runnable snapshot at that chapter's stage. The canonical full-featured version lives in **ch11/nanocode.py** (767 lines). The test suite is in **ch09/test_nanocode.py**.

### Core Abstractions

**Brain** — pluggable LLM provider interface. Three implementations: `ClaudeBrain`, `DeepSeekBrain`, `OllamaBrain`. Each wraps `request_with_retry()` and returns a `Thought(text, tool_calls, raw_content)`. The `raw_content` field is fed back into conversation history verbatim (API format varies per provider).

**Tool** — each tool implements `execute(context: ToolContext, **args) -> str`. `ToolContext` carries the current mode (`plan`/`act`) and the `Memory` object. Tools blocked in plan mode (`WriteFile`, `EditFile`, `RunCommand`) raise an error when called.

**Agent** — owns the conversation list and the agentic loop. `handle_input()` detects slash commands, appends user message, then calls `_agentic_loop()` (max 50 iterations): think → append raw response → execute tools → feed results back → repeat until no tool calls.

**Memory** — persists to `.nanocode/memory.md`. Loaded on startup and injected as the `system` prompt on every API call. Updated via the `SaveMemory` tool.

### Agentic Loop Flow

```
user input → agent.handle_input()
  → _agentic_loop() [≤50 iterations]
      → brain.think(conversation)       # API call
      → append raw_content to history
      → if tool_calls: execute each → append results → loop
      → else: break, return text output
```

### Context Compaction

Each Brain tracks `last_input_tokens`. When usage exceeds 75% of the model's `context_limit` (Claude: 200k, DeepSeek: 128k, Ollama: 32k), `_compact_conversation()` summarizes old messages into a single assistant turn to stay within limits.

### Tools (ch11)

`ReadFile`, `WriteFile`, `EditFile`, `ListFiles`, `SearchCodebase`, `SaveMemory`, `RunCommand`, `SearchWeb`

### Chapter Progression

| Chapter | Key Addition |
|---------|-------------|
| ch01 | REPL skeleton (no AI) |
| ch03 | Stateful Claude chatbot |
| ch04 | DeepSeek multi-provider |
| ch05 | File tools (Read/Write/Edit) |
| ch06 | Persistent Memory |
| ch07 | Plan mode (safety harness) |
| ch08 | ListFiles + SearchCodebase |
| ch09 | RunCommand + full agentic loop + tests |
| ch10 | Ollama + context compaction |
| ch11 | SearchWeb (DuckDuckGo) — final version |
| ch12 | Capstone demo with `snake_game/` |

## Testing

Tests use a `FakeBrain` that returns scripted `Thought` responses — no API key needed. The test suite (ch09) covers the agentic loop, tool execution, mode enforcement, memory persistence, and compaction. When adding features, mirror the chapter where they were introduced (e.g., new tools → ch11 level).
