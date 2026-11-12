"""Small SQLite helpers for SmartMeal.

The app is intentionally single-user and stores its data on this computer.
Keeping database work here makes the Streamlit pages easier to read.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Iterator


DEFAULT_DB_PATH = Path(__file__).with_name("smartmeal.db")

COIN_REWARDS = {
    "meal": (4, 16),
    "water": (3, 9),
    "activity": (6, 12),
    "checkin": (5, 5),
}


def get_db_path() -> Path:
    """Return the database path, with an override for isolated tests."""
    return Path(os.environ.get("SMARTMEAL_DB_PATH", str(DEFAULT_DB_PATH)))


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    """Open a connection and always close it after the operation."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the tables the first time the app runs."""
    with database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                height_cm REAL NOT NULL,
                weight_kg REAL NOT NULL,
                activity_level TEXT NOT NULL,
                health_goal TEXT NOT NULL,
                egg_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_date TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                food_name TEXT NOT NULL,
                servings REAL NOT NULL,
                calories REAL NOT NULL,
                protein_g REAL NOT NULL,
                carbs_g REAL NOT NULL,
                fat_g REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS water_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                amount_ml INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                duration_min INTEGER NOT NULL,
                calories_burned INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weight_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS xp_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                xp INTEGER NOT NULL,
                description TEXT NOT NULL,
                UNIQUE (source_type, source_id)
            );

            CREATE TABLE IF NOT EXISTS coin_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT NOT NULL,
                UNIQUE (source_type, source_id)
            );

            CREATE TABLE IF NOT EXISTS pet_status (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                happiness INTEGER NOT NULL DEFAULT 72,
                energy INTEGER NOT NULL DEFAULT 76,
                affection INTEGER NOT NULL DEFAULT 60,
                last_action TEXT NOT NULL DEFAULT 'Ready for a little care',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS owned_decorations (
                item_key TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                purchased_at TEXT NOT NULL,
                equipped INTEGER NOT NULL DEFAULT 1 CHECK (equipped IN (0, 1))
            );
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO pet_status (
                id, happiness, energy, affection, last_action, updated_at
            ) VALUES (1, 72, 76, 60, 'Ready for a little care', ?)
            """,
            (date.today().isoformat(),),
        )


def get_profile() -> dict[str, Any] | None:
    with database() as connection:
        row = connection.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return dict(row) if row else None


def save_profile(values: dict[str, Any]) -> None:
    """Create or update the single local profile."""
    today = date.today().isoformat()
    with database() as connection:
        existing = connection.execute(
            "SELECT id FROM profile WHERE id = 1"
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE profile
                SET name = ?, age = ?, gender = ?, height_cm = ?, weight_kg = ?,
                    activity_level = ?, health_goal = ?, egg_type = ?, updated_at = ?
                WHERE id = 1
                """,
                (
                    values["name"],
                    values["age"],
                    values["gender"],
                    values["height_cm"],
                    values["weight_kg"],
                    values["activity_level"],
                    values["health_goal"],
                    values["egg_type"],
                    today,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO profile (
                    id, name, age, gender, height_cm, weight_kg,
                    activity_level, health_goal, egg_type, created_at, updated_at
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    values["name"],
                    values["age"],
                    values["gender"],
                    values["height_cm"],
                    values["weight_kg"],
                    values["activity_level"],
                    values["health_goal"],
                    values["egg_type"],
                    today,
                    today,
                ),
            )
            connection.execute(
                "INSERT INTO weight_entries (entry_date, weight_kg, created_at) "
                "VALUES (?, ?, ?)",
                (today, values["weight_kg"], today),
            )


def _award_xp(
    connection: sqlite3.Connection,
    source_type: str,
    source_id: str,
    entry_date: str,
    xp: int,
    description: str,
    daily_limit: int,
) -> int:
    """Award XP for a logged action, up to that action's daily limit."""
    already_recorded = connection.execute(
        "SELECT 1 FROM xp_events WHERE source_type = ? AND source_id = ?",
        (source_type, source_id),
    ).fetchone()
    if already_recorded:
        return 0

    earned_today = connection.execute(
        "SELECT COALESCE(SUM(xp), 0) FROM xp_events "
        "WHERE source_type = ? AND entry_date = ?",
        (source_type, entry_date),
    ).fetchone()[0]
    amount = min(xp, max(0, daily_limit - int(earned_today)))
    if amount == 0:
        return 0

    connection.execute(
        """
        INSERT INTO xp_events (source_type, source_id, entry_date, xp, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (source_type, source_id, entry_date, amount, description),
    )
    return amount


def _award_coins(
    connection: sqlite3.Connection,
    source_type: str,
    source_id: str,
    entry_date: str,
    description: str,
) -> int:
    """Award a modest number of coins for healthy logging, with daily caps."""
    reward, daily_limit = COIN_REWARDS[source_type]
    already_recorded = connection.execute(
        "SELECT 1 FROM coin_events WHERE source_type = ? AND source_id = ?",
        (source_type, source_id),
    ).fetchone()
    if already_recorded:
        return 0

    earned_today = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM coin_events "
        "WHERE source_type = ? AND entry_date = ?",
        (source_type, entry_date),
    ).fetchone()[0]
    amount = min(reward, max(0, daily_limit - int(earned_today)))
    if amount == 0:
        return 0

    connection.execute(
        """
        INSERT INTO coin_events (source_type, source_id, entry_date, amount, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (source_type, source_id, entry_date, amount, description),
    )
    return amount


def add_meal(
    meal_date: str,
    meal_type: str,
    food_name: str,
    servings: float,
    calories: float,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
) -> int:
    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO meals (
                meal_date, meal_type, food_name, servings, calories,
                protein_g, carbs_g, fat_g, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meal_date,
                meal_type,
                food_name,
                servings,
                calories,
                protein_g,
                carbs_g,
                fat_g,
                date.today().isoformat(),
            ),
        )
        xp_awarded = _award_xp(
            connection,
            "meal",
            str(cursor.lastrowid),
            meal_date,
            8,
            "Logged a meal",
            32,
        )
        _award_coins(
            connection, "meal", str(cursor.lastrowid), meal_date, "Logged a meal"
        )
        return xp_awarded


def add_water(entry_date: str, amount_ml: int) -> int:
    if not 1 <= amount_ml <= 5000:
        raise ValueError("Water amount must be between 1 and 5,000 ml.")
    with database() as connection:
        cursor = connection.execute(
            "INSERT INTO water_entries (entry_date, amount_ml, created_at) "
            "VALUES (?, ?, ?)",
            (entry_date, amount_ml, date.today().isoformat()),
        )
        xp_awarded = _award_xp(
            connection,
            "water",
            str(cursor.lastrowid),
            entry_date,
            3,
            "Logged water",
            9,
        )
        _award_coins(
            connection, "water", str(cursor.lastrowid), entry_date, "Logged water"
        )
        return xp_awarded


def add_activity(
    entry_date: str,
    activity_type: str,
    duration_min: int,
    calories_burned: int,
) -> int:
    if not 1 <= duration_min <= 600:
        raise ValueError("Activity duration must be between 1 and 600 minutes.")
    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO activities (
                entry_date, activity_type, duration_min, calories_burned, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry_date,
                activity_type,
                duration_min,
                max(0, calories_burned),
                date.today().isoformat(),
            ),
        )
        xp_awarded = _award_xp(
            connection,
            "activity",
            str(cursor.lastrowid),
            entry_date,
            10,
            "Logged movement",
            20,
        )
        _award_coins(
            connection,
            "activity",
            str(cursor.lastrowid),
            entry_date,
            "Logged movement",
        )
        return xp_awarded


def add_weight(entry_date: str, weight_kg: float) -> None:
    if not 20 <= weight_kg <= 300:
        raise ValueError("Weight must be between 20 and 300 kg.")
    with database() as connection:
        connection.execute(
            "INSERT INTO weight_entries (entry_date, weight_kg, created_at) "
            "VALUES (?, ?, ?)",
            (entry_date, weight_kg, date.today().isoformat()),
        )
        latest = connection.execute(
            "SELECT entry_date FROM weight_entries ORDER BY entry_date DESC, id DESC LIMIT 1"
        ).fetchone()
        if latest and entry_date >= latest["entry_date"]:
            connection.execute(
                "UPDATE profile SET weight_kg = ?, updated_at = ? WHERE id = 1",
                (weight_kg, date.today().isoformat()),
            )


def record_daily_checkin(entry_date: str) -> bool:
    with database() as connection:
        awarded = _award_xp(
            connection,
            "checkin",
            entry_date,
            entry_date,
            5,
            "Completed a gentle daily check-in",
            5,
        )
        if awarded:
            _award_coins(
                connection,
                "checkin",
                entry_date,
                entry_date,
                "Completed a gentle daily check-in",
            )
    return awarded > 0


def has_daily_checkin(entry_date: str) -> bool:
    with database() as connection:
        row = connection.execute(
            "SELECT 1 FROM xp_events WHERE source_type = 'checkin' AND source_id = ?",
            (entry_date,),
        ).fetchone()
    return row is not None


def get_total_xp() -> int:
    with database() as connection:
        return int(
            connection.execute("SELECT COALESCE(SUM(xp), 0) FROM xp_events").fetchone()[0]
        )


def get_total_coins() -> int:
    with database() as connection:
        total = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM coin_events"
        ).fetchone()[0]
    return max(0, int(total))


def get_pet_status() -> dict[str, Any]:
    with database() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO pet_status (
                id, happiness, energy, affection, last_action, updated_at
            ) VALUES (1, 72, 76, 60, 'Ready for a little care', ?)
            """,
            (date.today().isoformat(),),
        )
        row = connection.execute(
            "SELECT * FROM pet_status WHERE id = 1"
        ).fetchone()
    return dict(row)


def interact_with_pet(action: str) -> dict[str, Any]:
    """Persist a pet-care action without granting XP or coins."""
    changes = {
        "play": (12, -14, 2, "Played together"),
        "sleep": (5, 24, 1, "Had a cozy nap"),
        "attention": (6, 0, 14, "Received some gentle attention"),
    }
    if action not in changes:
        raise ValueError("Choose play, sleep, or attention.")

    happiness_change, energy_change, affection_change, label = changes[action]
    with database() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO pet_status (
                id, happiness, energy, affection, last_action, updated_at
            ) VALUES (1, 72, 76, 60, 'Ready for a little care', ?)
            """,
            (date.today().isoformat(),),
        )
        current = connection.execute(
            "SELECT happiness, energy, affection FROM pet_status WHERE id = 1"
        ).fetchone()
        happiness = min(100, max(0, int(current["happiness"]) + happiness_change))
        energy = min(100, max(0, int(current["energy"]) + energy_change))
        affection = min(100, max(0, int(current["affection"]) + affection_change))
        connection.execute(
            """
            UPDATE pet_status
            SET happiness = ?, energy = ?, affection = ?, last_action = ?, updated_at = ?
            WHERE id = 1
            """,
            (happiness, energy, affection, label, date.today().isoformat()),
        )
    return get_pet_status()


def list_owned_decorations() -> list[dict[str, Any]]:
    with database() as connection:
        rows = connection.execute(
            "SELECT item_key, category, purchased_at, equipped "
            "FROM owned_decorations ORDER BY category, item_key"
        ).fetchall()
    return [dict(row) for row in rows]


def purchase_decoration(
    item_key: str, category: str, price: int
) -> dict[str, Any]:
    """Buy and place a single decoration, atomically charging its coin cost."""
    if not item_key or not category or price <= 0:
        raise ValueError("Decoration details and a positive price are required.")

    with database() as connection:
        existing = connection.execute(
            "SELECT 1 FROM owned_decorations WHERE item_key = ?", (item_key,)
        ).fetchone()
        if existing:
            return {"ok": False, "reason": "owned"}

        balance = int(
            connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM coin_events"
            ).fetchone()[0]
        )
        if balance < price:
            return {"ok": False, "reason": "coins"}

        today = date.today().isoformat()
        connection.execute(
            "UPDATE owned_decorations SET equipped = 0 WHERE category = ?",
            (category,),
        )
        connection.execute(
            """
            INSERT INTO owned_decorations (item_key, category, purchased_at, equipped)
            VALUES (?, ?, ?, 1)
            """,
            (item_key, category, today),
        )
        connection.execute(
            """
            INSERT INTO coin_events (source_type, source_id, entry_date, amount, description)
            VALUES ('spend', ?, ?, ?, ?)
            """,
            (item_key, today, -price, f"Bought {item_key} room decor"),
        )
    return {"ok": True, "reason": ""}


def set_decoration_equipped(item_key: str, equipped: bool) -> bool:
    """Place or put away owned decor; only one item per category is active."""
    with database() as connection:
        row = connection.execute(
            "SELECT category FROM owned_decorations WHERE item_key = ?",
            (item_key,),
        ).fetchone()
        if row is None:
            return False
        if equipped:
            connection.execute(
                "UPDATE owned_decorations SET equipped = 0 WHERE category = ?",
                (row["category"],),
            )
        connection.execute(
            "UPDATE owned_decorations SET equipped = ? WHERE item_key = ?",
            (int(equipped), item_key),
        )
    return True


def get_daily_summary(entry_date: str) -> dict[str, float | int]:
    with database() as connection:
        meals = connection.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(calories), 0) AS calories,
                   COALESCE(SUM(protein_g), 0) AS protein_g,
                   COALESCE(SUM(carbs_g), 0) AS carbs_g,
                   COALESCE(SUM(fat_g), 0) AS fat_g
            FROM meals WHERE meal_date = ?
            """,
            (entry_date,),
        ).fetchone()
        water = connection.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(amount_ml), 0) AS amount_ml "
            "FROM water_entries WHERE entry_date = ?",
            (entry_date,),
        ).fetchone()
        activity = connection.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(duration_min), 0) AS duration_min,
                   COALESCE(SUM(calories_burned), 0) AS calories_burned
            FROM activities WHERE entry_date = ?
            """,
            (entry_date,),
        ).fetchone()
    return {
        "meal_count": int(meals["count"]),
        "calories": float(meals["calories"]),
        "protein_g": float(meals["protein_g"]),
        "carbs_g": float(meals["carbs_g"]),
        "fat_g": float(meals["fat_g"]),
        "water_count": int(water["count"]),
        "water_ml": int(water["amount_ml"]),
        "activity_count": int(activity["count"]),
        "activity_min": int(activity["duration_min"]),
        "activity_calories": int(activity["calories_burned"]),
    }


def list_meals(entry_date: str) -> list[dict[str, Any]]:
    with database() as connection:
        rows = connection.execute(
            "SELECT * FROM meals WHERE meal_date = ? ORDER BY id DESC",
            (entry_date,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_water_entries(entry_date: str) -> list[dict[str, Any]]:
    with database() as connection:
        rows = connection.execute(
            "SELECT * FROM water_entries WHERE entry_date = ? ORDER BY id DESC",
            (entry_date,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_activities(entry_date: str) -> list[dict[str, Any]]:
    with database() as connection:
        rows = connection.execute(
            "SELECT * FROM activities WHERE entry_date = ? ORDER BY id DESC",
            (entry_date,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_weights() -> list[dict[str, Any]]:
    with database() as connection:
        rows = connection.execute(
            "SELECT * FROM weight_entries ORDER BY entry_date, id"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_record(record_type: str, record_id: int) -> None:
    """Delete one visible log entry and revoke XP tied to that entry."""
    table_names = {
        "meal": "meals",
        "water": "water_entries",
        "activity": "activities",
        "weight": "weight_entries",
    }
    table_name = table_names.get(record_type)
    if table_name is None:
        raise ValueError("Unknown record type.")

    with database() as connection:
        connection.execute(
            "DELETE FROM xp_events WHERE source_type = ? AND source_id = ?",
            (record_type, str(record_id)),
        )
        connection.execute(
            "DELETE FROM coin_events WHERE source_type = ? AND source_id = ?",
            (record_type, str(record_id)),
        )
        connection.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        if record_type == "weight":
            latest = connection.execute(
                "SELECT weight_kg FROM weight_entries "
                "ORDER BY entry_date DESC, id DESC LIMIT 1"
            ).fetchone()
            if latest:
                connection.execute(
                    "UPDATE profile SET weight_kg = ?, updated_at = ? WHERE id = 1",
                    (latest["weight_kg"], date.today().isoformat()),
                )


def load_demo_profile() -> None:
    """Fill a blank database with clearly labeled, fictional demo records."""
    if get_profile() is not None:
        return

    save_profile(
        {
            "name": "Ploy",
            "age": 21,
            "gender": "Female",
            "height_cm": 160,
            "weight_kg": 58,
            "activity_level": "light",
            "health_goal": "maintenance",
            "egg_type": "cat",
        }
    )

    today = date.today()
    for days_ago, weight in [(21, 57.7), (14, 58.0), (7, 57.8)]:
        add_weight((today.fromordinal(today.toordinal() - days_ago)).isoformat(), weight)

    day = today.isoformat()
    add_meal(day, "Breakfast", "Thai omelette with rice", 1, 430, 18, 51, 17)
    add_meal(day, "Lunch", "Chicken pad kra pao with rice", 1, 560, 30, 68, 16)
    add_water(day, 350)
    add_water(day, 400)
    add_activity(day, "Brisk walk", 30, 101)
    record_daily_checkin(day)
