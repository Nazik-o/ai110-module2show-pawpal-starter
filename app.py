import streamlit as st

from pawpal_system import FREQUENCIES, PRIORITIES, Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks for the day.")

# Streamlit reruns this script on every interaction, so keep the Owner in the
# session "vault" and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = st.number_input(
        "Minutes available today", min_value=0, max_value=1440, value=owner.available_minutes
    )

st.divider()

st.subheader("Pets")
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
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Tasks")
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
                    task_title.strip(),
                    task_time.strftime("%H:%M"),
                    int(duration),
                    priority,
                    frequency,
                )
                owner.get_pet(task_pet).add_task(task)
                st.success(f"Added '{task.description}' for {task_pet} at {task.time}.")
            except ValueError as err:
                st.error(str(err))

    tasks = scheduler.sort_by_time()
    if tasks:
        st.table(
            [
                {
                    "time": t.time,
                    "pet": t.pet_name,
                    "task": t.description,
                    "minutes": t.duration_minutes,
                    "priority": t.priority,
                    "repeats": t.frequency,
                    "done": "✅" if t.completed else "",
                }
                for t in tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")
