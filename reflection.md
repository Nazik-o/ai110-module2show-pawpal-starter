# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three core actions a user should be able to perform:

1. **Add a pet**: enter the owner's info and register one or more pets (name, species, age).
2. **Schedule a care task**: give a pet a task such as a walk, feeding, or medication, with a time, duration, priority, and how often it repeats.
3. **See today's plan**: view today's tasks in time order, get warned about clashes, and get a plan that fits the owner's available time.

My initial UML (`diagrams/uml.mmd`) has four classes:

- **Task** (dataclass): one care activity. Holds description, time (`"HH:MM"`), duration, priority, frequency, due date, and completion status. Its own behavior is just `mark_complete()`.
- **Pet** (dataclass): stores pet details plus its list of `Task`s. Responsible for adding tasks and reporting how many it has.
- **Owner**: holds the owner's name, how many minutes they have available per day, and their `Pet`s. Its key method is `get_all_tasks()`, which flattens every pet's tasks into one list.
- **Scheduler**: the "brain". It holds a reference to an `Owner` and only reads tasks through `Owner.get_all_tasks()`, so it naturally works across multiple pets. It sorts, filters, completes tasks, and detects conflicts.

Relationships: Owner 1 → * Pet, Pet 1 → * Task, Scheduler → Owner.

**b. Design changes**

Yes. When I reviewed the skeleton, two gaps stood out:

1. **Tasks didn't know which pet they belonged to.** Because the Scheduler gets a flat list from `Owner.get_all_tasks()`, it had no way to say *whose* walk was conflicting, or to put the next occurrence of a recurring task back on the right pet. I added a `pet_name` field to `Task` that `Pet.add_task()` fills in automatically, so the user never has to type it twice.
2. **There was no way to express "the plan".** The scenario asks the app to fit tasks into the owner's available time and explain its choices, and a plain list can't carry "why". I added a small `DailyPlan` dataclass (scheduled tasks, skipped tasks, a reason per task, total minutes) and a `Scheduler.build_daily_plan()` method that produces it.

I also added input validation in `Task.__post_init__` (time must be `HH:MM`, priority and frequency must be known values). Sorting compares `"HH:MM"` strings, so a value like `"9:00"` would silently sort after `"10:00"`. Rejecting it early is safer.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:

- **Time of day**: every task has an `"HH:MM"` start time and a duration, used for ordering and for spotting overlaps.
- **Due date and recurrence**: only tasks due on the chosen day are planned. Daily and weekly tasks regenerate when completed.
- **Priority** (high / medium / low): decides what gets dropped when there isn't enough time.
- **The owner's time budget** (`Owner.available_minutes`): the total minutes of care the owner can give that day.
- **Completion status**: finished tasks are excluded from conflicts and from the plan.

I ranked **priority above time** when building the plan. Missing a medication or a meal is worse than missing grooming, so the plan should protect the essentials first and only then fill remaining time. Time of day is still used for the final ordering, because that's how an owner actually reads a plan.

**b. Tradeoffs**

**Greedy planning, not optimal packing.** `build_daily_plan()` walks tasks from highest to lowest priority and keeps each one that still fits in the remaining minutes. It never backtracks, so it never trades one higher-priority task for a better overall mix. For example, with 30 minutes left, a 30-minute medium task takes the whole slot, even if the owner would rather fit three 10-minute low-priority tasks. Getting the best mix is a knapsack problem. For a pet owner, though, "the high-priority things always come first" is easier to trust and explain than an optimizer that sometimes drops a medium task to squeeze in lower ones. The simple greedy rule also produces a clear one-line reason for every decision.

**Conflicts are warnings, not blockers.** `detect_conflicts()` checks real overlapping windows (start + duration), not just identical start times, but it only *reports* them. It doesn't move tasks or refuse to save them. Some "conflicts" are fine in real life (e.g., giving a cat its pill during breakfast), so the owner is better placed than the program to decide. The check is also pairwise (O(n²)), which is perfectly fast for the handful of tasks a household has per day.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code as an agent inside VS Code for the whole build. I gave it the full project brief and asked it to read the starter repo and produce a plan before writing code. It came back with questions about my git setup and which optional challenges to include, then a phase-by-phase plan. After I approved the plan, it worked through the phases: UML and class skeletons, the core classes and CLI demo, Streamlit wiring, the algorithms, tests, and docs. It ran `main.py`, `pytest`, and a scripted Streamlit session after each phase and committed each phase separately.

The most effective features were:
- **Planning before coding.** Having the agent read the requirements and existing files and write a plan I could approve kept it from jumping straight into code.
- **Running and verifying its own work.** It ran the demo, the tests, and a headless Streamlit session (`AppTest`), so problems surfaced as real failures rather than guesses.
- **Multi-file edits.** Features like recurrence touched `Task`, `Scheduler`, `main.py`, the tests, and the README together.

The most helpful prompts were concrete and scoped, like "make sure everything runs end to end", plus clear answers to its clarifying questions (e.g., choosing priority + time-budget scheduling as my extension instead of JSON persistence).

**b. Judgment and verification**

- **Conflict detection design.** The brief suggests a lightweight exact-time match. The plan I approved goes further and checks real overlap (start + duration), because a 30-minute walk at 07:30 clashes with an 08:00 task in practice, not only when the start times are identical. I kept the "warn, don't crash" approach rather than auto-rescheduling, because a pill at breakfast is a "conflict" an owner may want.
- **Scope.** The plan offered JSON persistence and extra formatting as extensions. I chose only priority + time-budget scheduling to keep the design focused on the scenario's "fit tasks to available time and explain why".
- **Tests that were wrong, not code.** Twice during the UI tests, an assertion failed. Once a plan expected a skipped task, but after completing the morning walk everything genuinely fit in 60 minutes. Once a test compared `"08:00-08:10"` against `"08:00-08:05"` for two tasks that both start at 08:00. In both cases we worked the numbers by hand to confirm the scheduler was right and the expectation was wrong before changing anything.
- **Demo output.** The first algorithmic `main.py` printed tomorrow's recurring walk in the "still to do" list with no date, which looked like a duplicate. We added a date column.

I verified suggestions by running `python main.py` and reading the output line by line, by running `python -m pytest` after each change, and by checking key numbers (budget math, `timedelta` dates) by hand.

---

## 4. Testing and Verification

**a. What you tested**

30 tests in total. `tests/test_pawpal.py` covers the core classes (`mark_complete`, `add_task` count, `Owner.get_all_tasks` across pets, input validation), chronological and priority sorting, pet/status filters, daily/weekly/one-off recurrence (including completing twice and overdue tasks), conflict detection (same time, overlapping durations, and no false positives for back-to-back tasks, other days, or completed tasks), and the budgeted daily plan. `tests/test_app.py` drives the actual Streamlit page through its forms and buttons.

These matter because the scheduler's value is in rules that are easy to get subtly wrong. String-sorting `"9:00"` vs `"10:00"`, off-by-one recurrence dates, a duplicate follow-up task, or a false conflict alarm would all "run fine" but give an owner the wrong plan. The UI tests matter because Streamlit reruns the script on every click, and losing the `Owner` from `st.session_state` is a classic bug that unit tests can't see.

**b. Confidence**

About 4 out of 5. Every rule I implemented has happy-path and edge-case tests, and the CLI and UI both run cleanly. Next I'd test:
- Tasks that cross midnight (e.g., 23:45 for 30 minutes), which currently aren't compared against the next day's early tasks.
- Very large numbers of tasks (performance of the O(n²) conflict check).
- Two pets with the same name, and editing or deleting tasks once the UI supports it.
- Completing a recurring task days early, and what "next occurrence" should mean then.

---

## 5. Reflection

**a. What went well**

The explainable daily plan. `build_daily_plan()` doesn't just output a list; it says *why* each task made the cut or didn't ("medium priority; needs 30 min but only 15 min left"). That directly answers the scenario's "explain why it chose that plan", and it made the logic easy to debug. I'm also happy that the `Scheduler` only ever talks to `Owner.get_all_tasks()`, so multi-pet support came for free.

**b. What you would improve**

- Persist data to `data.json` so pets and tasks survive closing the app.
- Let users edit and delete tasks in the UI, and suggest the next free time slot when a conflict is detected.
- Give tasks a stable `id` instead of keying plan reasons by Python `id()`, which would also make persistence and editing simpler.
- Handle tasks that span midnight.

**c. Key takeaway**

Being the "lead architect" means owning the decisions and the verification, not the keystrokes. The AI could write a working scheduler quickly, but the important calls were mine to make: what counts as a conflict, whether priority beats time, warn vs. block, and what to leave out. The UML-first, CLI-first workflow made those decisions visible early. Insisting on running the demo and tests after every step was what caught the mistakes, including the AI's mistakes in its own tests. Writing a plan up front and committing phase by phase served the same purpose as separate chat sessions: each phase had a clear goal and a checkpoint, so it was easy to see what changed and why.
