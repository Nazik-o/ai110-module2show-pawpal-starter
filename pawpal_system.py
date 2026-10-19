"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

import re
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

PRIORITIES = ("low", "medium", "high")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = ("once", "daily", "weekly")
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


@dataclass
class Task:
    """A single pet care activity."""

    description: str
    time: str  # "HH:MM", 24-hour clock
    duration_minutes: int = 15
    priority: str = "medium"  # low | medium | high
    frequency: str = "once"  # once | daily | weekly
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""  # filled in by Pet.add_task()

    def __post_init__(self):
        """Validate fields so bad input fails early instead of mis-sorting later."""
        if not TIME_PATTERN.match(self.time):
            raise ValueError(f"time must be HH:MM (24-hour), got {self.time!r}")
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> "Task | None":
        """Return a fresh copy due on the next repeat date, or None for one-off tasks."""
        if self.frequency not in FREQUENCY_DAYS:
            return None
        # Count from today if the task was overdue, so the next one isn't already in the past.
        base = max(self.due_date, date.today())
        return replace(self, due_date=base + timedelta(days=FREQUENCY_DAYS[self.frequency]), completed=False)

    def start_minutes(self) -> int:
        """Return the start time as minutes after midnight."""
        hours, minutes = self.time.split(":")
        return int(hours) * 60 + int(minutes)

    def end_minutes(self) -> int:
        """Return the end time as minutes after midnight."""
        return self.start_minutes() + self.duration_minutes

    def time_range(self) -> str:
        """Return the task's window formatted like '07:30-08:00'."""
        end = self.end_minutes() % (24 * 60)
        return f"{self.time}-{end // 60:02d}:{end % 60:02d}"


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def task_count(self) -> int:
        """Return how many tasks this pet has."""
        return len(self.tasks)


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if there isn't one."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class DailyPlan:
    """The result of Scheduler.build_daily_plan(): what fits today, what doesn't, and why."""

    day: date
    available_minutes: int
    scheduled: list[Task] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)
    reasons: dict[int, str] = field(default_factory=dict)  # keyed by id(task)
    total_minutes: int = 0

    def reason_for(self, task: Task) -> str:
        """Return the explanation recorded for a task."""
        return self.reasons.get(id(task), "")


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def _tasks(self, tasks: list[Task] | None) -> list[Task]:
        """Use the given tasks, or fall back to every task the owner has."""
        return self.owner.get_all_tasks() if tasks is None else tasks

    def get_tasks_for_date(self, day: date | None = None) -> list[Task]:
        """Return all of the owner's tasks due on the given day (default: today)."""
        day = day or date.today()
        return [t for t in self.owner.get_all_tasks() if t.due_date == day]

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks in chronological order (by date, then "HH:MM" time)."""
        # Zero-padded "HH:MM" strings sort correctly as plain strings.
        return sorted(self._tasks(tasks), key=lambda t: (t.due_date, t.time))

    def sort_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks ordered high -> low priority, breaking ties by time."""
        return sorted(self._tasks(tasks), key=lambda t: (PRIORITY_RANK[t.priority], t.due_date, t.time))

    def filter_by_pet(self, pet_name: str, tasks: list[Task] | None = None) -> list[Task]:
        """Return only the tasks for the named pet."""
        return [t for t in self._tasks(tasks) if t.pet_name == pet_name]

    def filter_by_status(self, completed: bool, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in self._tasks(tasks) if t.completed == completed]

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task; for daily/weekly tasks, add and return the next occurrence."""
        if task.completed:
            return None  # completing twice must not spawn duplicate follow-ups
        task.mark_complete()
        follow_up = task.next_occurrence()
        pet = self.owner.get_pet(task.pet_name)
        if follow_up and pet:
            pet.add_task(follow_up)
            return follow_up
        return None

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning for every pair of pending tasks whose time windows overlap on the same day."""
        pending = self.sort_by_time(self.filter_by_status(False, tasks))
        warnings = []
        for i, first in enumerate(pending):
            for second in pending[i + 1:]:
                if second.due_date != first.due_date or second.start_minutes() >= first.end_minutes():
                    continue
                if first.time == second.time:
                    detail = f"both start at {first.time}"
                else:
                    detail = f"{first.time_range()} overlaps {second.time_range()}"
                warnings.append(
                    f"Conflict on {first.due_date}: {first.pet_name} '{first.description}' and "
                    f"{second.pet_name} '{second.description}' ({detail})"
                )
        return warnings

    def build_daily_plan(self, day: date | None = None) -> DailyPlan:
        """Greedily fit the day's pending tasks into the owner's time budget, highest priority first."""
        day = day or date.today()
        plan = DailyPlan(day=day, available_minutes=self.owner.available_minutes)
        pending = self.filter_by_status(False, self.get_tasks_for_date(day))
        for task in self.sort_by_priority(pending):
            remaining = plan.available_minutes - plan.total_minutes
            if task.duration_minutes <= remaining:
                plan.scheduled.append(task)
                plan.total_minutes += task.duration_minutes
                plan.reasons[id(task)] = (
                    f"{task.priority} priority; fits in budget "
                    f"({plan.total_minutes}/{plan.available_minutes} min used)"
                )
            else:
                plan.skipped.append(task)
                plan.reasons[id(task)] = (
                    f"{task.priority} priority; needs {task.duration_minutes} min "
                    f"but only {remaining} min left"
                )
        plan.scheduled = self.sort_by_time(plan.scheduled)
        return plan
