import streamlit as st

from pawpal_system import FREQUENCIES, PRIORITIES, Owner, Pet, Scheduler, Task

PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks for the day.")

# Streamlit reruns this script on every interaction, so keep the Owner in the
# session "vault" and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)
    st.session_state.show_plan = False

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)


def task_label(task: Task) -> str:
    """Short text used to pick a task in a selectbox."""
    return f"{task.due_date:%b %d} {task.time} · {task.pet_name} · {task.description}"


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into rows for st.table."""
    return [
        {
            "date": f"{t.due_date:%b %d}",
            "time": t.time_range(),
            "pet": t.pet_name,
            "task": t.description,
            "minutes": t.duration_minutes,
            "priority": PRIORITY_BADGE[t.priority],
            "repeats": t.frequency,
            "status": "✅ done" if t.completed else "⏳ to do",
        }
        for t in tasks
    ]


# --- Owner ------------------------------------------------------------------
st.subheader("👤 Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input("Minutes available today", min_value=0, max_value=1440, value=owner.available_minutes)
    )

st.divider()

# --- Pets -------------------------------------------------------------------
st.subheader("🐶 Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=3)
    if st.form_submit_button("Add pet"):
        name = pet_name.strip()
        if not name:
            st.error("Pet name can't be empty.")
        elif owner.get_pet(name):
            st.error(f"{name} is already registered.")
        else:
            owner.add_pet(Pet(name, species, int(age)))
            st.success(f"Added {name}.")

if owner.pets:
    st.table([{"name": p.name, "species": p.species, "age": p.age, "tasks": p.task_count()} for p in owner.pets])
else:
    st.info("No pets yet. Add one above to start scheduling.")

st.divider()

# --- Tasks ------------------------------------------------------------------
st.subheader("📋 Tasks")
if not owner.pets:
    st.caption("Add a pet before scheduling tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_pet = st.selectbox("Pet", [p.name for p in owner.pets])
            task_title = st.text_input("Task", value="Morning walk")
            task_time = st.time_input("Time", step=300)
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", PRIORITIES, index=PRIORITIES.index("high"))
            frequency = st.selectbox("Repeats", FREQUENCIES)
        if st.form_submit_button("Add task"):
            try:
                task = Task(
                    task_title.strip() or "Untitled task",
                    task_time.strftime("%H:%M"),
                    int(duration),
                    priority,
                    frequency,
                )
                owner.get_pet(task_pet).add_task(task)
                st.success(f"Added '{task.description}' for {task_pet} at {task.time}.")
            except ValueError as err:
                st.error(str(err))

    pending = scheduler.sort_by_time(scheduler.filter_by_status(False))
    if pending:
        col1, col2 = st.columns([3, 1])
        with col1:
            choice = st.selectbox(
                "Mark a task complete", range(len(pending)), format_func=lambda i: task_label(pending[i])
            )
        with col2:
            st.write("")  # aligns the button with the selectbox
            if st.button("Complete ✔"):
                done = pending[choice]
                follow_up = scheduler.mark_task_complete(done)
                st.success(f"Marked '{done.description}' for {done.pet_name} complete.")
                if follow_up:
                    st.info(f"🔁 Repeats {follow_up.frequency}: next one added for {follow_up.due_date:%a %b %d}.")

    if owner.get_all_tasks():
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
        with col2:
            status_filter = st.radio("Status", ["To do", "Done", "All"], horizontal=True)
        with col3:
            sort_order = st.radio("Sort by", ["Time", "Priority"], horizontal=True)

        shown = owner.get_all_tasks()
        if pet_filter != "All pets":
            shown = scheduler.filter_by_pet(pet_filter, shown)
        if status_filter != "All":
            shown = scheduler.filter_by_status(status_filter == "Done", shown)
        shown = scheduler.sort_by_time(shown) if sort_order == "Time" else scheduler.sort_by_priority(shown)

        if shown:
            st.table(task_rows(shown))
        else:
            st.info("No tasks match these filters.")

        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.markdown("**⚠️ Scheduling conflicts**")
            for warning in conflicts:
                st.warning(f"{warning}. Consider moving one of these tasks.")
        else:
            st.success("No scheduling conflicts. Every pending task has its own time slot.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Today's plan -----------------------------------------------------------
st.subheader("🗓️ Today's Schedule")
st.caption("Fits today's to-do tasks into your available minutes, highest priority first.")

if st.button("Generate schedule", type="primary"):
    st.session_state.show_plan = True

if st.session_state.show_plan:
    plan = scheduler.build_daily_plan()
    if not plan.scheduled and not plan.skipped:
        st.info("Nothing left to do today. 🎉")
    else:
        st.success(
            f"Planned {len(plan.scheduled)} task(s) using {plan.total_minutes} of "
            f"{plan.available_minutes} available minutes."
        )
        if plan.scheduled:
            st.table([{**row, "why": plan.reason_for(t)} for row, t in zip(task_rows(plan.scheduled), plan.scheduled)])
        for task in plan.skipped:
            st.info(f"⏭️ Skipped {task.pet_name}'s '{task.description}': {plan.reason_for(task)}.")
        for warning in scheduler.detect_conflicts(plan.scheduled):
            st.warning(f"{warning}. These overlap in today's plan.")
