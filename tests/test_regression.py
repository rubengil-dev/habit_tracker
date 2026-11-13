"""
Regression: the demo data (always the same) must keep giving the same streaks and badges:
    - A change in the badge or streak rules that moves any of them makes this fail
    - If the change is on purpose, update the expected values below after checking them by hand
"""

# Imports
from sqlalchemy import select

from app.models import Badge, Habit
from app.services.history import load_history
from app.services.streaks import habit_streaks
from scripts.seed_dev import seed
from tests.helpers import TODAY

# Habit → (sessions, current streak, best streak), on TODAY
STREAKS = {
    "Correr":       (43, 0, 4),             # Today is a Monday: this week is still open
    "Leer":         (72, 2, 17),
    "Gimnasio":     (15, 2, 4),
    "Fumar":        (2, 19, 20),            # Avoid mode: days without smoking
    "Crochet":      (4, 0, 3),              # Inactive: its streak broke long ago
}

# (habit, badge) → (value, tier), on TODAY
BADGES = {
    ("Correr", "Kilómetros"):           (358.7,             "silver"),
    ("Correr", "Mejor ritmo"):          (291.826923077,     "silver"),      # Seconds per km, lower is better
    ("Correr", "Diez o más"):           (9,                 "bronze"),
    ("Correr", "Bajo la lluvia"):       (9,                 "silver"),
    ("Correr", "Semanas de 3"):         (4,                 "bronze"),
    ("Leer", "Páginas leídas"):         (1532,              "silver"),
    ("Leer", "Días leyendo"):           (72,                "silver"),
    ("Leer", "Racha lectora"):          (17,                "silver"),
    ("Gimnasio", "Días de gimnasio"):   (15,                "silver"),
    ("Gimnasio", "Semanas cumplidas"):  (6,                 "bronze"),
    ("Fumar", "Días limpios"):          (58,                "silver"),
    ("Fumar", "Racha limpia"):          (20,                "silver"),
    ("Crochet", "Proyectos"):           (4,                 "bronze"),
}


def test_demo_streaks_unchanged(db):
    """Sessions, current and best streak of every demo habit."""
    demo = seed(db, "a long password", TODAY)
    db.commit()

    streaks = {}
    for habit in db.scalars(select(Habit).where(Habit.user_id == demo.id)):
        history = load_history(db, habit.id)
        streaks[habit.name] = (len(history), *habit_streaks(habit, history, TODAY))

    assert streaks == STREAKS


def test_demo_badges_unchanged(db):
    """Value and tier of every demo badge."""
    demo = seed(db, "a long password", TODAY)
    db.commit()

    rows = db.execute(select(Habit.name, Badge).join(Badge).where(Habit.user_id == demo.id))
    badges = {(habit, badge.name): (badge.current_value, badge.current_tier.value) for habit, badge in rows}

    assert badges == BADGES
