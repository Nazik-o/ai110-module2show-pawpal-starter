# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I gave Claude Code (agent mode in VS Code) the full project brief and asked it to plan and implement the required phases end to end. I added Challenge 1 + 3 as a third algorithmic capability: **priority-then-time scheduling inside the owner's daily time budget, with an explanation for each choice** (`Scheduler.build_daily_plan()`).

**What did the agent do?**

1. Read the brief and the starter repo, then asked me to choose the git workflow and which optional challenges to include before writing a plan.
2. Created `.venv`, installed `requirements.txt`, pointed `origin` at my fork, and untracked a stale `__pycache__` file that the starter had committed.
3. Wrote the draft UML (`diagrams/uml.mmd`) and the class skeleton, then implemented the classes in `pawpal_system.py`.
4. Built `main.py` and `tests/test_pawpal.py`, added `pytest.ini` so both `pytest` and `python -m pytest` can import the root module, and wired `app.py` to the classes via `st.session_state`.
5. Added the algorithms: `sort_by_time`, `sort_by_priority`, `filter_by_pet`/`filter_by_status`, `mark_task_complete` + `Task.next_occurrence` (recurrence), `detect_conflicts`, and `build_daily_plan` with the `DailyPlan` result.
6. Ran `python main.py`, `python -m pytest`, and a scripted Streamlit `AppTest` after each phase, and made one commit per phase.

Files modified: `pawpal_system.py`, `main.py`, `app.py`, `tests/test_pawpal.py`, `pytest.ini`, `diagrams/uml.mmd`, `diagrams/uml_final.mmd`, `README.md`, `reflection.md`, `ai_interactions.md`.

**What did you have to verify or fix manually?**

- **Push access:** `origin` still pointed at the CodePath upstream repo, so I supplied my fork URL. The agent couldn't use my GitHub credentials, so I push the commits myself.
- **Confusing demo output:** in the first algorithmic version of `main.py`, the auto-created "Morning walk" for tomorrow appeared in the "Still to do" list with no date, so it looked like a duplicate walk today. A due-date column fixed it.
- **Recurrence edge cases:** I checked that completing a task twice doesn't spawn two follow-ups, and that an overdue daily task's next copy is due tomorrow rather than another past date. Both now have tests.
- **Reflection review:** I read the reflection the agent drafted and edited it to describe my own experience.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
