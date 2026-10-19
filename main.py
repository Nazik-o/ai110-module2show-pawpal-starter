"""CLI demo for PawPal+: builds an owner with two pets and prints today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task(task: Task) -> str:
    """Return a one-line, human-readable description of a task."""
    status = "done" if task.completed else "todo"
    return (
        f"  {task.time}  {task.pet_name:<6} {task.description:<18} "
        f"{task.duration_minutes:>3} min  [{task.priority}]  ({task.frequency}, {status})"
    )


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    luna.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    mochi.add_task(Task("Vet appointment", "14:00", 45, "medium"))

    scheduler = Scheduler(owner)

    print(f"Today's Schedule for {owner.name}")
    print("=" * 40)
    for task in scheduler.sort_by_time():
        print(format_task(task))


if __name__ == "__main__":
    main()
