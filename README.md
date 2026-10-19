# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation summary

All logic lives in `pawpal_system.py`. It has four classes:

- **`Task`** (dataclass): one care activity, with description, `"HH:MM"` time, duration, priority, frequency, due date, completion status, and the name of the pet it belongs to.
- **`Pet`** (dataclass): pet details plus its list of tasks. `add_task()` attaches a task and tags it with the pet's name.
- **`Owner`**: the owner's name, their daily time budget (`available_minutes`), and their pets. `get_all_tasks()` returns every pet's tasks as one list.
- **`Scheduler`**: the "brain". It takes an `Owner` and always reads tasks through `Owner.get_all_tasks()`, so every feature works across all pets at once.

`main.py` is a CLI demo that builds an owner with two pets and prints today's schedule. `app.py` is the Streamlit UI on top of the same classes.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output of `python main.py`:

```
Today's Schedule for Jordan
========================================
  07:30  Mochi  Morning walk        30 min  [high]  (daily, todo)
  08:00  Luna   Breakfast           10 min  [high]  (daily, todo)
  14:00  Mochi  Vet appointment     45 min  [medium]  (once, todo)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite (from the project root, with .venv activated):
python -m pytest
```

`pytest.ini` puts the project root on the import path, so plain `pytest` works too.

The suite in `tests/test_pawpal.py` covers:

- **Core classes**: `mark_complete()` flips status, `Pet.add_task()` increases the task count and tags the pet, and `Owner.get_all_tasks()` combines every pet's tasks. Invalid input (e.g. `"9:00"`, unknown priority, zero duration) is rejected.
- **Sorting**: tasks come back in chronological order (date first, then time), and priority sort puts high before medium before low, breaking ties by time.
- **Filtering**: by pet name and by completion status, including an unknown pet.
- **Recurrence**: completing a daily task creates a new one due tomorrow; weekly creates one due in 7 days; one-off tasks create nothing; completing twice doesn't duplicate; an overdue daily task rolls forward from today.
- **Conflict detection**: same start time across pets, overlapping durations, and no false alarms for back-to-back tasks, different days, or completed tasks.
- **Daily plan**: respects the time budget, keeps high-priority tasks first, explains skipped tasks, and only plans today's pending tasks.
- **Edge cases**: an owner whose pets have no tasks yields empty sorts, no conflicts, and an empty plan.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/norazgulyyev/Downloads/Codepath/ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 25 items

tests/test_pawpal.py .........................                           [100%]

============================== 25 passed in 0.02s ==============================
```

**Confidence level: ★★★★☆ (4/5).** Every scheduling rule (sorting, filtering, recurrence, conflicts, budgeted planning) has passing happy-path and edge-case tests. I'm holding back one star because the Streamlit UI is only covered by a scripted smoke test, not the unit suite, and some cases aren't modeled at all: tasks that cross midnight, and time zones.

## 📐 Smarter Scheduling

All scheduling logic lives on `Scheduler` in `pawpal_system.py` and reads tasks through `Owner.get_all_tasks()`, so it works across every pet.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting (time) | `Scheduler.sort_by_time()` | `sorted()` with `key=lambda t: (t.due_date, t.time)`. Zero-padded `"HH:MM"` strings sort correctly as text, and `Task` validates that format on creation. |
| Task sorting (priority) | `Scheduler.sort_by_priority()` | High → medium → low via a `PRIORITY_RANK` lookup, ties broken by time. |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()`, `Scheduler.get_tasks_for_date()` | Filter by pet name, done/not done, or due date. Filters accept an optional task list, so they can be chained. |
| Conflict handling | `Scheduler.detect_conflicts()` | Compares every pair of *pending* tasks on the same date and flags any whose `[start, start + duration)` windows overlap, which includes exact same-time clashes. Returns warning strings instead of raising, so the app never crashes on a clash. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a `daily` or `weekly` task automatically adds a fresh copy to the same pet, due today + 1 or + 7 days (`timedelta`). Completing a task twice doesn't create duplicates. |
| Time-budget plan *(Challenge 1 + 3)* | `Scheduler.build_daily_plan()` → `DailyPlan` | Takes today's pending tasks in priority order and keeps each one that still fits in `Owner.available_minutes`. The result lists scheduled tasks (in time order), skipped tasks, and a one-line reason for every decision. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
