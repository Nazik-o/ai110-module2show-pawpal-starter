"""CLI demo for PawPal+: exercises sorting, filtering, recurrence, conflicts, and planning."""

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task(task: Task) -> str:
    """Return a one-line, human-readable description of a task."""
    status = "done" if task.completed else "todo"
    return (
        f"  {task.due_date:%b %d} {task.time}  {task.pet_name:<6} {task.description:<16} "
        f"{task.duration_minutes:>3} min  {'[' + task.priority + ']':<8}  {task.frequency:<6}  {status}"
    )


def print_section(title: str, tasks: list[Task]) -> None:
    """Print a titled block of tasks (or a placeholder if there are none)."""
    print(f"\n{title}")
    print("-" * len(title))
    for task in tasks:
        print(format_task(task))
    if not tasks:
        print("  (none)")


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of time order.
    mochi.add_task(Task("Vet appointment", "14:00", 45, "medium"))
    luna.add_task(Task("Brush coat", "19:00", 15, "low", "weekly"))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    luna.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Give medication", "08:00", 5, "high", "daily"))  # same time as Breakfast
    mochi.add_task(Task("Evening walk", "18:30", 30, "medium", "daily"))

    scheduler = Scheduler(owner)

    print(f"Today's Schedule for {owner.name} (sorted by time)")
    print("=" * 45)
    for task in scheduler.sort_by_time():
        print(format_task(task))

    print_section("Mochi's tasks (filter_by_pet)", scheduler.sort_by_time(scheduler.filter_by_pet("Mochi")))

    print("\nConflict check (detect_conflicts)")
    print("---------------------------------")
    for warning in scheduler.detect_conflicts() or ["No conflicts found."]:
        print(f"  WARNING: {warning}" if warning.startswith("Conflict") else f"  {warning}")

    walk = next(t for t in mochi.tasks if t.description == "Morning walk")
    follow_up = scheduler.mark_task_complete(walk)
    print("\nRecurring task (mark_task_complete)")
    print("-----------------------------------")
    print(f"  Completed '{walk.description}' due {walk.due_date}")
    print(f"  Next '{follow_up.description}' automatically created for {follow_up.due_date}")

    print_section("Completed tasks (filter_by_status)", scheduler.filter_by_status(True))
    print_section("Still to do (filter_by_status)", scheduler.sort_by_time(scheduler.filter_by_status(False)))

    plan = scheduler.build_daily_plan()
    print(f"\nToday's plan: {plan.total_minutes}/{plan.available_minutes} min (build_daily_plan)")
    print("-" * 45)
    for task in plan.scheduled:
        print(f"{format_task(task)}\n      why: {plan.reason_for(task)}")
    for task in plan.skipped:
        print(f"  SKIPPED {task.pet_name} '{task.description}': {plan.reason_for(task)}")


if __name__ == "__main__":
    main()
