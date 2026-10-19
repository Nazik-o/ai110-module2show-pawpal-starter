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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
