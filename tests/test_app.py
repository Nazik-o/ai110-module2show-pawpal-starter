"""End-to-end tests that drive the Streamlit UI in app.py with Streamlit's AppTest."""

import datetime

import pytest
from streamlit.testing.v1 import AppTest


def run(at: AppTest) -> AppTest:
    """Rerun the app and fail on any uncaught exception."""
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def widget(widgets, label):
    """Return the widget with the given label."""
    return next(w for w in widgets if w.label == label)


def add_pet(at, name, species):
    widget(at.text_input, "Pet name").set_value(name)
    widget(at.selectbox, "Species").set_value(species)
    widget(at.button, "Add pet").click()
    return run(at)


def add_task(at, pet, title, hhmm, minutes, priority, frequency):
    widget(at.selectbox, "Pet").set_value(pet)
    widget(at.text_input, "Task").set_value(title)
    at.time_input[0].set_value(datetime.time(*map(int, hhmm.split(":"))))
    widget(at.number_input, "Duration (minutes)").set_value(minutes)
    widget(at.selectbox, "Priority").set_value(priority)
    widget(at.selectbox, "Repeats").set_value(frequency)
    widget(at.button, "Add task").click()
    return run(at)


@pytest.fixture
def app():
    """The app with two pets and a few tasks, including a same-time conflict."""
    at = run(AppTest.from_file("../app.py", default_timeout=30))
    add_pet(at, "Mochi", "dog")
    add_pet(at, "Luna", "cat")
    add_task(at, "Mochi", "Evening walk", "18:30", 30, "medium", "daily")
    add_task(at, "Mochi", "Morning walk", "07:30", 30, "high", "daily")
    add_task(at, "Luna", "Breakfast", "08:00", 10, "high", "daily")
    add_task(at, "Luna", "Medication", "08:00", 5, "high", "once")
    add_task(at, "Luna", "Brush coat", "19:00", 15, "low", "weekly")
    return at


def test_pets_and_tasks_are_stored_on_the_owner(app):
    owner = app.session_state.owner
    assert [p.name for p in owner.pets] == ["Mochi", "Luna"]
    assert len(owner.get_all_tasks()) == 5


def test_duplicate_pet_is_rejected(app):
    add_pet(app, "Mochi", "dog")
    assert any("already registered" in e.value for e in app.error)
    assert len(app.session_state.owner.pets) == 2


def test_task_table_is_sorted_and_conflicts_are_warned(app):
    starts = [window[:5] for window in app.table[-1].value["time"]]
    assert starts == ["07:30", "08:00", "08:00", "18:30", "19:00"]
    assert any("Breakfast" in w.value and "Medication" in w.value for w in app.warning)


def test_completing_daily_task_adds_next_occurrence(app):
    picker = widget(app.selectbox, "Mark a task complete")
    picker.set_value(next(i for i, label in enumerate(picker.options) if "Morning walk" in label))
    widget(app.button, "Complete ✔").click()
    run(app)
    assert any("next one added" in i.value for i in app.info)
    assert len(app.session_state.owner.get_all_tasks()) == 6

    widget(app.radio, "Status").set_value("Done")
    run(app)
    assert list(app.table[-1].value["task"]) == ["Morning walk"]


def test_generated_plan_respects_budget_and_explains_skips(app):
    widget(app.number_input, "Minutes available today").set_value(60)
    run(app)
    widget(app.button, "Generate schedule").click()
    run(app)
    assert any("using 60 of 60 available minutes" in s.value for s in app.success)
    plan = app.table[-1].value
    assert list(plan["task"]) == ["Morning walk", "Breakfast", "Medication", "Brush coat"]
    assert all(plan["why"])
    assert any("Skipped Mochi's 'Evening walk'" in i.value for i in app.info)
