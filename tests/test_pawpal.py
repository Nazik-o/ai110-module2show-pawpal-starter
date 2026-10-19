"""Tests for the PawPal+ logic layer."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date.today()


@pytest.fixture
def household():
    """An owner with two pets and no tasks yet."""
    owner = Owner("Jordan", available_minutes=60)
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))
    return owner


# --- Core behaviour ---------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert pet.task_count() == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert pet.task_count() == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_owner_get_all_tasks_combines_every_pet(household):
    household.get_pet("Mochi").add_task(Task("Walk", "07:30"))
    household.get_pet("Luna").add_task(Task("Breakfast", "08:00"))
    descriptions = {t.description for t in Scheduler(household).sort_by_time()}
    assert descriptions == {"Walk", "Breakfast"}


def test_pet_with_no_tasks_is_handled(household):
    scheduler = Scheduler(household)
    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []
    plan = scheduler.build_daily_plan()
    assert plan.scheduled == [] and plan.skipped == [] and plan.total_minutes == 0


@pytest.mark.parametrize(
    "kwargs",
    [{"time": "9:00"}, {"time": "25:00"}, {"priority": "urgent"}, {"frequency": "monthly"}, {"duration_minutes": 0}],
)
def test_invalid_task_input_is_rejected(kwargs):
    fields = {"description": "Walk", "time": "09:00", **kwargs}
    with pytest.raises(ValueError):
        Task(**fields)


# --- Sorting ----------------------------------------------------------------

def test_sort_by_time_returns_chronological_order(household):
    mochi, luna = household.pets
    mochi.add_task(Task("Dinner", "18:00"))
    luna.add_task(Task("Breakfast", "08:00"))
    mochi.add_task(Task("Lunch walk", "12:30"))
    luna.add_task(Task("Early meds", "06:45"))
    times = [t.time for t in Scheduler(household).sort_by_time()]
    assert times == ["06:45", "08:00", "12:30", "18:00"]


def test_sort_by_time_orders_by_date_before_time(household):
    mochi = household.get_pet("Mochi")
    mochi.add_task(Task("Tomorrow early", "06:00", due_date=TODAY + timedelta(days=1)))
    mochi.add_task(Task("Today late", "21:00"))
    assert [t.description for t in Scheduler(household).sort_by_time()] == ["Today late", "Tomorrow early"]


def test_sort_by_priority_then_time(household):
    mochi = household.get_pet("Mochi")
    mochi.add_task(Task("Brush", "07:00", priority="low"))
    mochi.add_task(Task("Vet", "15:00", priority="high"))
    mochi.add_task(Task("Meds", "09:00", priority="high"))
    mochi.add_task(Task("Play", "08:00", priority="medium"))
    order = [t.description for t in Scheduler(household).sort_by_priority()]
    assert order == ["Meds", "Vet", "Play", "Brush"]


# --- Filtering --------------------------------------------------------------

def test_filter_by_pet_and_status(household):
    mochi, luna = household.pets
    walk = Task("Walk", "07:30")
    mochi.add_task(walk)
    luna.add_task(Task("Breakfast", "08:00"))
    scheduler = Scheduler(household)
    walk.mark_complete()

    assert [t.description for t in scheduler.filter_by_pet("Mochi")] == ["Walk"]
    assert [t.description for t in scheduler.filter_by_status(True)] == ["Walk"]
    assert [t.description for t in scheduler.filter_by_status(False)] == ["Breakfast"]
    assert scheduler.filter_by_pet("Nobody") == []


# --- Recurrence -------------------------------------------------------------

def test_completing_daily_task_creates_next_day_task(household):
    mochi = household.get_pet("Mochi")
    walk = Task("Walk", "07:30", frequency="daily")
    mochi.add_task(walk)

    follow_up = Scheduler(household).mark_task_complete(walk)

    assert walk.completed is True
    assert follow_up is not None
    assert follow_up.due_date == TODAY + timedelta(days=1)
    assert follow_up.completed is False
    assert follow_up.time == "07:30" and follow_up.pet_name == "Mochi"
    assert mochi.task_count() == 2


def test_completing_weekly_task_creates_task_one_week_later(household):
    luna = household.get_pet("Luna")
    brush = Task("Brush coat", "19:00", frequency="weekly")
    luna.add_task(brush)
    follow_up = Scheduler(household).mark_task_complete(brush)
    assert follow_up.due_date == TODAY + timedelta(days=7)


def test_completing_one_off_task_creates_nothing(household):
    mochi = household.get_pet("Mochi")
    vet = Task("Vet", "14:00")
    mochi.add_task(vet)
    assert Scheduler(household).mark_task_complete(vet) is None
    assert mochi.task_count() == 1


def test_completing_twice_does_not_duplicate_follow_up(household):
    mochi = household.get_pet("Mochi")
    walk = Task("Walk", "07:30", frequency="daily")
    mochi.add_task(walk)
    scheduler = Scheduler(household)
    scheduler.mark_task_complete(walk)
    assert scheduler.mark_task_complete(walk) is None
    assert mochi.task_count() == 2


def test_overdue_daily_task_rolls_forward_from_today(household):
    mochi = household.get_pet("Mochi")
    walk = Task("Walk", "07:30", frequency="daily", due_date=TODAY - timedelta(days=3))
    mochi.add_task(walk)
    follow_up = Scheduler(household).mark_task_complete(walk)
    assert follow_up.due_date == TODAY + timedelta(days=1)


# --- Conflict detection -----------------------------------------------------

def test_detects_duplicate_times_across_pets(household):
    household.get_pet("Mochi").add_task(Task("Walk", "08:00"))
    household.get_pet("Luna").add_task(Task("Breakfast", "08:00"))
    warnings = Scheduler(household).detect_conflicts()
    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Breakfast" in warnings[0] and "08:00" in warnings[0]


def test_detects_overlapping_durations(household):
    mochi = household.get_pet("Mochi")
    mochi.add_task(Task("Walk", "07:30", duration_minutes=45))
    mochi.add_task(Task("Grooming", "08:00", duration_minutes=15))
    assert len(Scheduler(household).detect_conflicts()) == 1


def test_back_to_back_tasks_do_not_conflict(household):
    mochi = household.get_pet("Mochi")
    mochi.add_task(Task("Walk", "07:30", duration_minutes=30))
    mochi.add_task(Task("Breakfast", "08:00", duration_minutes=10))
    assert Scheduler(household).detect_conflicts() == []


def test_same_time_on_different_days_is_not_a_conflict(household):
    mochi = household.get_pet("Mochi")
    mochi.add_task(Task("Walk", "08:00"))
    mochi.add_task(Task("Walk", "08:00", due_date=TODAY + timedelta(days=1)))
    assert Scheduler(household).detect_conflicts() == []


def test_completed_tasks_are_ignored_by_conflict_check(household):
    walk = Task("Walk", "08:00")
    household.get_pet("Mochi").add_task(walk)
    household.get_pet("Luna").add_task(Task("Breakfast", "08:00"))
    walk.mark_complete()
    assert Scheduler(household).detect_conflicts() == []


# --- Daily plan (time budget + priority) ------------------------------------

def test_daily_plan_respects_budget_and_priority(household):
    mochi, luna = household.pets  # budget is 60 minutes
    mochi.add_task(Task("Walk", "07:30", 30, "high"))
    luna.add_task(Task("Meds", "20:00", 5, "high"))
    mochi.add_task(Task("Training", "10:00", 40, "medium"))
    luna.add_task(Task("Brush", "19:00", 15, "low"))

    plan = Scheduler(household).build_daily_plan()

    assert [t.description for t in plan.scheduled] == ["Walk", "Brush", "Meds"]  # time order
    assert [t.description for t in plan.skipped] == ["Training"]
    assert plan.total_minutes == 50 <= household.available_minutes
    assert "only 25 min left" in plan.reason_for(plan.skipped[0])
    assert all(plan.reason_for(t) for t in plan.scheduled)


def test_daily_plan_only_includes_pending_tasks_for_that_day(household):
    mochi = household.get_pet("Mochi")
    done = Task("Done already", "07:00")
    done.mark_complete()
    mochi.add_task(done)
    mochi.add_task(Task("Tomorrow", "08:00", due_date=TODAY + timedelta(days=1)))
    mochi.add_task(Task("Today", "09:00"))
    plan = Scheduler(household).build_daily_plan()
    assert [t.description for t in plan.scheduled] == ["Today"]
