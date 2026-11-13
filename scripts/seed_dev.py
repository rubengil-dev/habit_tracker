"""
Fills the development database with a demo user and months of history, to try the front with real-looking data:
    Run from the project root: uv run python -m scripts.seed_dev
    Uses the database in DATABASE_URL (.env), after typing the Neon branch name to confirm it is dev
    The demo user is rebuilt from scratch on every run; nobody else's data is touched
"""

# Imports
import datetime as dt
import random
import sys
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_engine
from app.enums import BadgeKind, GoalMode, MetricKind, Period, TagRule
from app.models import Badge, BadgeTag, Entry, EntryValue, Habit, Metric, Tag, User
from app.services.badges import recalculate_badges
from app.services.periods import local_today
from app.services.ratios import refresh_ratios
from app.services.tiers import is_count, suggest_tiers
from scripts.create_user import read_password, save_user

# Who and how much
USERNAME = "demo"
RANDOM_SEED = 2026                          # Same data on every run
CONFIRMATION = "dev"                        # Neon branch name to type before writing


def main():
    """Entry point: confirms the database, asks for the demo password and rebuilds the demo user."""
    confirm_dev_database()
    password = read_password()

    with Session(get_engine()) as db:
        seed(db, password)
        db.commit()

    print(f"User {USERNAME} rebuilt with 5 habits and their history.")


def seed(db: Session, password: str, today: dt.date | None = None) -> User:
    """Demo user rebuilt with its habits, sessions and badges, all recalculated; the caller commits."""
    random.seed(RANDOM_SEED)
    remove_demo_user(db)
    user = save_user(db, USERNAME, password)
    db.flush()

    today = today or local_today(user.timezone)
    for build in (build_running, build_reading, build_gym, build_smoking, build_crochet):
        habit = build(db, user, today)
        db.flush()
        recalculate_badges(db, habit, today)

    return user


def confirm_dev_database():
    """The person running it types the Neon branch name; anything else stops the script."""
    host = make_url(get_settings().database_url).host
    answer = input(f"Database host: {host}\nThe demo user will be rebuilt there. Type the Neon branch name to confirm: ")

    if answer.strip().lower() != CONFIRMATION:
        sys.exit(f"Nothing changed: this script only runs on the {CONFIRMATION} branch.")


def remove_demo_user(db: Session):
    """Demo user deleted with everything in it (cascade), so every run starts clean."""
    db.execute(delete(User).where(User.username == USERNAME))
    db.flush()


# Habits

def build_running(db: Session, user: User, today: dt.date) -> Habit:
    """Running 3 times a week for 4 months: km, time and pace, rain and tired tags, five kinds of badge."""
    habit = add_habit(db, user, "Correr", today - dt.timedelta(days=120), 3, Period.WEEKLY)
    km = add_metric(db, habit, "Distancia", MetricKind.NUMBER, unit="km")
    time = add_metric(db, habit, "Tiempo", MetricKind.DURATION)
    pace = add_metric(db, habit, "Ritmo", MetricKind.RATIO, unit="s/km", operands=(time, km))
    rain, tired = add_tag(db, habit, "Lluvia"), add_tag(db, habit, "Cansado")
    db.flush()

    for day in days_between(habit.start_date, today):
        if day.weekday() in (0, 2, 5) and random.random() < 0.85:
            distance = round(random.uniform(5, 12), 1)
            seconds = round(distance * random.uniform(290, 360))
            tags = [tag for tag, chance in ((rain, 0.2), (tired, 0.25)) if random.random() < chance]
            add_entry(db, habit, day, {km: distance, time: seconds}, tags, ratios=[pace])

    add_badge(db, habit, "Kilómetros", BadgeKind.HISTORIC, 10, 2000, metric=km)
    add_badge(db, habit, "Mejor ritmo", BadgeKind.RECORD, 360, 270, metric=pace, higher_is_better=False)
    add_badge(db, habit, "Diez o más", BadgeKind.OBJECTIVE, 1, 100, metric=km, threshold=10)
    add_badge(db, habit, "Bajo la lluvia", BadgeKind.HISTORIC, 1, 50, required=[rain])
    add_badge(db, habit, "Semanas de 3", BadgeKind.STREAK, 1, 52, period=Period.WEEKLY, target=3, mode=GoalMode.MIN)
    return habit


def build_reading(db: Session, user: User, today: dt.date) -> Habit:
    """Reading most days for 3 months: pages, daily consistency and streak."""
    habit = add_habit(db, user, "Leer", today - dt.timedelta(days=90), 1, Period.DAILY)
    pages = add_metric(db, habit, "Páginas", MetricKind.NUMBER, unit="páginas")
    db.flush()

    for day in days_between(habit.start_date, today):
        if random.random() < 0.8:
            add_entry(db, habit, day, {pages: random.randint(5, 40)})

    add_badge(db, habit, "Páginas leídas", BadgeKind.HISTORIC, 50, 20000, metric=pages)
    add_badge(db, habit, "Días leyendo", BadgeKind.CONSISTENCY, 1, 365, period=Period.DAILY, target=1, mode=GoalMode.MIN)
    add_badge(db, habit, "Racha lectora", BadgeKind.STREAK, 1, 100, period=Period.DAILY, target=1, mode=GoalMode.MIN)
    return habit


def build_gym(db: Session, user: User, today: dt.date) -> Habit:
    """Gym twice a week for 2 months, yes/no only: sessions without values."""
    habit = add_habit(db, user, "Gimnasio", today - dt.timedelta(days=60), 2, Period.WEEKLY)

    for day in days_between(habit.start_date, today):
        if day.weekday() in (1, 3) and random.random() < 0.75:
            add_entry(db, habit, day)

    add_badge(db, habit, "Días de gimnasio", BadgeKind.HISTORIC, 1, 200)
    add_badge(db, habit, "Semanas cumplidas", BadgeKind.CONSISTENCY, 1, 52, period=Period.WEEKLY, target=2, mode=GoalMode.MIN)
    return habit


def build_smoking(db: Session, user: User, today: dt.date) -> Habit:
    """Not smoking for 2 months (avoid mode), with two slips: clean days and the best clean run."""
    habit = add_habit(db, user, "Fumar", today - dt.timedelta(days=60), 0, Period.DAILY, GoalMode.MAX)

    for days_ago in (41, 20):
        add_entry(db, habit, today - dt.timedelta(days=days_ago))

    add_badge(db, habit, "Días limpios", BadgeKind.CONSISTENCY, 1, 365, period=Period.DAILY, target=0, mode=GoalMode.MAX)
    add_badge(db, habit, "Racha limpia", BadgeKind.STREAK, 1, 100, period=Period.DAILY, target=0, mode=GoalMode.MAX)
    return habit


def build_crochet(db: Session, user: User, today: dt.date) -> Habit:
    """An inactive habit with a few old sessions: hidden from the daily view, history kept."""
    habit = add_habit(db, user, "Crochet", today - dt.timedelta(days=150), 1, Period.WEEKLY, active=False)

    for days_ago in (148, 140, 133, 120):
        add_entry(db, habit, today - dt.timedelta(days=days_ago))

    add_badge(db, habit, "Proyectos", BadgeKind.HISTORIC, 1, 50)
    return habit


# Rows

def add_habit(db: Session, user: User, name: str, start: dt.date, target: int, period: Period,
              mode: GoalMode = GoalMode.MIN, active: bool = True) -> Habit:
    """New habit of the demo user."""
    habit = Habit(user_id=user.id, name=name, start_date=start, goal_target=target, goal_period=period,
                  goal_mode=mode, active=active)
    db.add(habit)
    db.flush()
    return habit


def add_metric(db: Session, habit: Habit, name: str, kind: MetricKind, unit: str | None = None,
               operands: tuple[Metric, Metric] | None = None) -> Metric:
    """New metric; a ratio takes its two operands (A ÷ B)."""
    a, b = operands or (None, None)
    metric = Metric(habit_id=habit.id, name=name, kind=kind, unit=unit,
                    operand_a_id=a and a.id, operand_b_id=b and b.id)
    db.add(metric)
    db.flush()
    return metric


def add_tag(db: Session, habit: Habit, name: str) -> Tag:
    """New tag."""
    tag = Tag(habit_id=habit.id, name=name)
    db.add(tag)
    return tag


def add_entry(db: Session, habit: Habit, day: dt.date, values: dict | None = None, tags: list | None = None,
              ratios: list | None = None):
    """New session with its typed-in values (metric → value), tags, and ratios calculated from them."""
    entry = Entry(habit_id=habit.id, date=day, tags=tags or [],
                  values=[EntryValue(metric_id=metric.id, value=value) for metric, value in (values or {}).items()])
    refresh_ratios(entry, ratios or [])
    db.add(entry)


def add_badge(db: Session, habit: Habit, name: str, kind: BadgeKind, first: float, diamond: float,
              metric: Metric | None = None, required: list | None = None, **fields):
    """New badge with the suggested thresholds between first and diamond (whole numbers in counts)."""
    badge = Badge(habit_id=habit.id, name=name, kind=kind, metric_id=metric and metric.id,
                  higher_is_better=fields.pop("higher_is_better", True), untagged_only=False,
                  tag_rules=[BadgeTag(tag_id=tag.id, rule=TagRule.REQUIRED) for tag in required or []], **fields)
    tiers = suggest_tiers(first, diamond, whole=is_count(badge))
    badge.unlocked, badge.bronze, badge.silver, badge.gold, badge.diamond = tiers
    db.add(badge)


def days_between(first: dt.date, last: dt.date) -> list[dt.date]:
    """Every day from first to last, both included."""
    return [first + dt.timedelta(days=offset) for offset in range((last - first).days + 1)]


if __name__ == "__main__":
    main()
