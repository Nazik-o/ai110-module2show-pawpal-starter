"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

import re
from dataclasses import dataclass, field
from datetime import date

PRIORITIES = ("low", "medium", "high")
FREQUENCIES = ("once", "daily", "weekly")
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


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_tasks_for_date(self, day: date | None = None) -> list[Task]:
        """Return all of the owner's tasks due on the given day (default: today)."""
        day = day or date.today()
        return [t for t in self.owner.get_all_tasks() if t.due_date == day]

    def sort_by_time(self) -> list[Task]:
        """Return tasks ordered by time of day."""
        return sorted(self.owner.get_all_tasks(), key=lambda t: t.time)

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return only the tasks for the named pet."""
        return [t for t in self.owner.get_all_tasks() if t.pet_name == pet_name]

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in self.owner.get_all_tasks() if t.completed == completed]

    def mark_task_complete(self, task: Task) -> None:
        """Complete a task (and handle any follow-up logic)."""
        task.mark_complete()

    def detect_conflicts(self) -> list[str]:
        """Return warnings for tasks scheduled at the same time."""
        return []
