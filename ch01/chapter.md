# Chapter 1: The Event Loop — The Skeleton

> *"Before a building has walls, it has a frame. Before a coding agent has intelligence, it has a loop."*

## What We're Building

By the end of this book, you'll have a working AI coding agent — a program that reads your files, writes code, runs shell commands, and thinks for itself. It will feel almost alive.

But we're not starting there. We're starting with 47 lines of Python and a loop that does almost nothing.

This is deliberate. Every skyscraper starts with a steel skeleton before the glass goes in. Every operating system starts with a scheduler before the apps. We're going to build our agent the same way — frame first, flesh later.

By the end of this chapter, you'll have:
- A running program that accepts user input
- An `Agent` class that processes it
- A clean way to quit
- A test suite that verifies all three

No AI yet. That comes in Chapter 2. First, let's get the bones right.

---

## The Anatomy of an Interactive Program

Every interactive program — a terminal, a game, a chatbot — runs the same fundamental pattern under the hood:

```
┌──────────────────────────────────────────┐
│              THE EVENT LOOP              │
│                                          │
│   ┌─────────┐    ┌─────────┐            │
│   │  Wait   │───▶│ Process │            │
│   │ for     │    │ Input   │            │
│   │ Input   │◀───│         │            │
│   └─────────┘    └─────────┘            │
│         ▲              │                │
│         │         until exit            │
│         │              ▼                │
│         │        ┌─────────┐            │
│         └────────│  Show   │            │
│                  │ Output  │            │
│                  └─────────┘            │
└──────────────────────────────────────────┘
```

Wait for input → process it → show output → repeat.

Your shell does this. Python's REPL does this. VS Code's command palette does this. And Nanocode will do this too — except the "process" step will eventually involve a large language model, file I/O, and shell commands.

The loop itself, though? It never changes. That's why we build it first.

---

## The Code, Line by Line

Here's the complete `ch01/nanocode.py`:

```python
# --- Exceptions ---

class AgentStop(Exception):
    """Raised when the agent should stop processing."""
    pass


# --- Agent Class ---

class Agent:
    """A coding agent that processes user input."""

    def __init__(self):
        pass

    def handle_input(self, user_input):
        """Handle user input. Returns output string, raises AgentStop to quit."""
        if user_input.strip() == "/q":
            raise AgentStop()

        if not user_input.strip():
            return ""

        return f"You said: {user_input}\n(Agent not yet connected)"


# --- Main Loop ---

def main():
    agent = Agent()
    print("⚡ Nanocode v0.1 initialized.")
    print("Type '/q' to quit.")

    while True:
        try:
            user_input = input("\n❯ ")
            output = agent.handle_input(user_input)
            if output:
                print(output)

        except (AgentStop, KeyboardInterrupt):
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
```

Let's walk through each section.

---

### The `AgentStop` Exception

```python
class AgentStop(Exception):
    """Raised when the agent should stop processing."""
    pass
```

This is a *sentinel exception* — a custom exception used not because something went wrong, but as a deliberate signal to stop.

Why use an exception instead of a return value or a flag? Because exceptions can be raised from anywhere — including deep inside nested function calls — and they'll bubble up cleanly to whatever is listening. When we add more layers to the agent in later chapters (tool calls, agentic loops, retries), any of those layers will still be able to stop everything by raising `AgentStop`. No flags to thread through, no return values to check at every level.

Think of it like a fire alarm: you don't have to walk through every room telling people to leave — you pull the alarm and everyone knows to exit.

---

### The `Agent` Class

```python
class Agent:
    def __init__(self):
        pass

    def handle_input(self, user_input):
        if user_input.strip() == "/q":
            raise AgentStop()

        if not user_input.strip():
            return ""

        return f"You said: {user_input}\n(Agent not yet connected)"
```

The `Agent` class is the heart of Nanocode. Right now it's nearly empty — `__init__` does nothing, and `handle_input` just echoes the input back. But the *shape* of the class is already correct.

`handle_input` has a clear contract:
- It **returns a string** — the agent's response to display to the user
- It **returns an empty string** for blank input (nothing to show)
- It **raises `AgentStop`** when the user wants to quit

This contract never changes, even when we replace the placeholder response with real AI output in Chapter 3. The main loop doesn't need to know *how* the agent thinks — it only needs to know what `handle_input` returns.

The two input guards deserve attention:

```python
if user_input.strip() == "/q":
    raise AgentStop()

if not user_input.strip():
    return ""
```

`.strip()` trims leading and trailing whitespace. This means `/q`, `  /q  `, and `/q\n` all quit cleanly. And `""`, `"   "`, and `"\n"` all return silently. We're being forgiving about what we accept — a user shouldn't have to worry about accidental spaces.

---

### The Main Loop

```python
def main():
    agent = Agent()
    print("⚡ Nanocode v0.1 initialized.")
    print("Type '/q' to quit.")

    while True:
        try:
            user_input = input("\n❯ ")
            output = agent.handle_input(user_input)
            if output:
                print(output)

        except (AgentStop, KeyboardInterrupt):
            print("\nExiting...")
            break
```

The main loop is the event loop described above, made concrete.

```
┌─────────────────────────────────────────────────────────┐
│                        main()                           │
│                                                         │
│  agent = Agent()          ← create once, reuse always   │
│                                                         │
│  while True:              ← loop forever (until exit)   │
│    user_input = input()   ← wait for user               │
│    output = agent.handle_input(user_input)              │
│    print(output)          ← show response               │
│                                                         │
│  except AgentStop         ← /q was typed                │
│  except KeyboardInterrupt ← Ctrl+C was pressed          │
│    break                  ← clean exit                  │
└─────────────────────────────────────────────────────────┘
```

A few design choices worth noting:

**`while True` with a `break`** — The loop runs until something explicitly stops it. There's no "running" boolean flag to track and no condition to evaluate each iteration. The exit signals (`AgentStop`, `KeyboardInterrupt`) come from outside the loop body, so they live in the `except` clause where they belong.

**`agent` is created once** — The `Agent` object is instantiated before the loop, not inside it. This means the agent persists across interactions. Starting in Chapter 3, it will accumulate conversation history. If we created a new `Agent` every iteration, it would forget everything between messages.

**Both exit paths are caught together** — `AgentStop` is raised by `/q`. `KeyboardInterrupt` is raised by `Ctrl+C`. Both mean "the user wants to stop," so they share the same handler. No duplication.

**`if __name__ == "__main__":`** — This guard ensures `main()` only runs when the script is executed directly (`python nanocode.py`), not when it's imported by a test. Without it, running the tests would immediately launch the agent and block waiting for input.

---

## Running It

```bash
python ch01/nanocode.py
```

```
⚡ Nanocode v0.1 initialized.
Type '/q' to quit.

❯ hello
You said: hello
(Agent not yet connected)

❯ 
❯ /q

Exiting...
```

Not impressive yet. But it runs, it responds, and it stops cleanly. That's the skeleton.

---

## The Tests

```python
import pytest
from nanocode import Agent, AgentStop


def test_handle_input_returns_string():
    agent = Agent()
    result = agent.handle_input("hello")
    assert isinstance(result, str)
    assert "hello" in result


def test_empty_input_returns_empty_string():
    agent = Agent()
    assert agent.handle_input("") == ""
    assert agent.handle_input("   ") == ""
    assert agent.handle_input("\n") == ""


def test_quit_command_raises_agent_stop():
    agent = Agent()
    with pytest.raises(AgentStop):
        agent.handle_input("/q")


def test_quit_command_with_whitespace():
    agent = Agent()
    with pytest.raises(AgentStop):
        agent.handle_input("  /q  ")
```

Four tests for 47 lines of code. Each tests one aspect of `handle_input`'s contract:

1. **Normal input** → returns a string containing the input
2. **Blank input** → returns `""` (three edge cases: empty, spaces, newline)
3. **`/q`** → raises `AgentStop`
4. **`/q` with whitespace** → still raises `AgentStop` (`.strip()` is doing its job)

Notice that none of these tests touch `main()`. The main loop is the "glue" that connects the agent to stdin/stdout — testing it would require mocking `input()` and `print()`. Instead, we've isolated the logic into `Agent.handle_input()`, which takes a plain string and returns a plain string (or raises). That makes it trivially testable.

This separation — logic in the class, I/O in `main()` — is a pattern we'll maintain throughout the book. Each time we add a feature, we add it to `Agent`, test it in isolation, and let `main()` stay thin.

Run the tests:

```bash
cd ch01
pytest test_nanocode.py -v
```

```
test_nanocode.py::test_handle_input_returns_string    PASSED
test_nanocode.py::test_empty_input_returns_empty_string PASSED
test_nanocode.py::test_quit_command_raises_agent_stop  PASSED
test_nanocode.py::test_quit_command_with_whitespace    PASSED

4 passed in 0.03s
```

No API key needed. No network calls. Just Python.

---

## How This Grows

Right now Nanocode looks like this:

```
User
  │
  │ types text
  ▼
main()  ──────────────────────────────▶  Agent.handle_input()
  │                                              │
  │ ◀────── returns string ─────────────────────┘
  │
  │ prints response
  ▼
User
```

By Chapter 11, the same diagram will look like this:

```
User
  │
  │ types text
  ▼
main()  ──▶  Agent.handle_input()
                    │
                    ▼
              _agentic_loop()
                    │
                    ├──▶  Brain.think()  ──▶  Claude API
                    │          │
                    │          ▼
                    │     ToolCall list
                    │          │
                    ├──▶  execute tools
                    │       ├── ReadFile
                    │       ├── WriteFile
                    │       ├── RunCommand
                    │       ├── SearchWeb
                    │       └── ...
                    │
                    └──▶  (loop until no tool calls)
                    │
                    ▼
              final response text
```

Every box in that second diagram — `Brain`, `_agentic_loop`, the tools — will be added one chapter at a time. The `main()` function and `Agent.handle_input()` structure you see now will barely change.

The skeleton you built in this chapter is load-bearing. Let's add some flesh.

---

## Summary

| Concept | What It Does |
|---------|-------------|
| `AgentStop` | Custom exception used as a stop signal — raises cleanly from anywhere |
| `Agent` class | Owns the agent's logic and (eventually) its state |
| `handle_input()` | Core contract: string in → string out, or `AgentStop` |
| `while True` loop | Runs forever until an exit signal is caught |
| `__name__ == "__main__"` | Prevents the loop from running when tests import the file |

**Next:** In Chapter 2, we'll make our first API call to Claude. No loop changes needed — just a quick script to verify our API key works and see what Claude responds with.
