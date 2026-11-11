"""SmartMeal — My Little Healthy Pet.

Run locally with: streamlit run app.py
"""

from __future__ import annotations

from datetime import date
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from smartmeal_data import (
    add_activity,
    add_meal,
    add_water,
    add_weight,
    delete_record,
    get_daily_summary,
    get_profile,
    get_total_xp,
    has_daily_checkin,
    initialize_database,
    list_activities,
    list_meals,
    list_water_entries,
    list_weights,
    load_demo_profile,
    record_daily_checkin,
    save_profile,
)


ACTIVITY_LEVELS = {
    "sedentary": ("Mostly sitting", 1.2),
    "light": ("Light activity", 1.375),
    "moderate": ("Moderate activity", 1.55),
    "very_active": ("Very active", 1.725),
}
GENDER_OPTIONS = ["Female", "Male", "Other / prefer not to say"]
GOAL_OPTIONS = {
    "weight_loss": "Weight loss",
    "maintenance": "Maintenance",
    "weight_gain": "Weight gain",
}
EGG_OPTIONS = {
    "cat": "Cat egg",
    "rabbit": "Rabbit egg",
    "dog": "Dog egg",
    "bear": "Bear egg",
    "penguin": "Penguin egg",
}
PET_FACES = {
    "cat": "🐱",
    "rabbit": "🐰",
    "dog": "🐶",
    "bear": "🐻",
    "penguin": "🐧",
}
PET_STAGES = [
    ("Egg", 0, 30, "A mystery egg, waiting for a little care."),
    ("Baby", 30, 90, "A tiny new friend has hatched."),
    ("Child", 90, 180, "Your pet is curious and growing."),
    ("Teen", 180, 300, "Your pet is getting stronger and more confident."),
    ("Adult", 300, None, "Your pet has grown into a healthy adult."),
]
WATER_GOAL_ML = 2000

THAI_FOODS: dict[str, dict[str, float]] = {
    "Chicken pad kra pao with rice": {
        "calories": 560,
        "protein": 30,
        "carbs": 68,
        "fat": 16,
    },
    "Thai omelette with rice": {
        "calories": 430,
        "protein": 18,
        "carbs": 51,
        "fat": 17,
    },
    "Chicken khao man gai": {
        "calories": 600,
        "protein": 28,
        "carbs": 72,
        "fat": 20,
    },
    "Shrimp pad Thai": {
        "calories": 520,
        "protein": 24,
        "carbs": 69,
        "fat": 16,
    },
    "Green curry chicken with rice": {
        "calories": 620,
        "protein": 28,
        "carbs": 76,
        "fat": 22,
    },
    "Tom yum goong": {
        "calories": 100,
        "protein": 15,
        "carbs": 6,
        "fat": 2,
    },
    "Som tam": {"calories": 120, "protein": 4, "carbs": 22, "fat": 3},
    "Chicken khao soi": {
        "calories": 650,
        "protein": 26,
        "carbs": 76,
        "fat": 28,
    },
    "Thai chicken satay (4 skewers)": {
        "calories": 280,
        "protein": 25,
        "carbs": 12,
        "fat": 14,
    },
    "Mango sticky rice": {
        "calories": 350,
        "protein": 5,
        "carbs": 70,
        "fat": 8,
    },
    "Fresh spring rolls (2 rolls)": {
        "calories": 180,
        "protein": 8,
        "carbs": 28,
        "fat": 4,
    },
    "Jasmine rice (1 bowl)": {
        "calories": 205,
        "protein": 4,
        "carbs": 45,
        "fat": 0.5,
    },
}

EXERCISES = {
    "Walking": 3.5,
    "Brisk walk": 4.3,
    "Running": 8.3,
    "Cycling": 6.8,
    "Swimming": 6.0,
    "Strength training": 5.0,
    "Yoga": 2.5,
    "Dancing": 5.5,
}


def calculate_calories(profile: dict[str, Any]) -> dict[str, float | None | str]:
    """Estimate adult BMR, TDEE, and a moderate daily target."""
    age = int(profile["age"])
    if age < 18:
        return {"bmr": None, "tdee": None, "target": None, "notice": "adult"}

    gender = profile["gender"]
    coefficient = {"Female": -161, "Male": 5}.get(gender, -78)
    bmr = (
        10 * float(profile["weight_kg"])
        + 6.25 * float(profile["height_cm"])
        - 5 * age
        + coefficient
    )
    activity_multiplier = ACTIVITY_LEVELS[profile["activity_level"]][1]
    tdee = bmr * activity_multiplier

    # Don't present a generic calorie target for unusually low or high estimates.
    if not 1500 <= tdee <= 4500:
        return {
            "bmr": round(bmr),
            "tdee": round(tdee),
            "target": None,
            "notice": "range",
        }

    goal = profile["health_goal"]
    if goal == "weight_loss":
        target = max(1500, tdee - 300)
    elif goal == "weight_gain":
        target = tdee + 250
    else:
        target = tdee

    notice = "floor" if goal == "weight_loss" and target == 1500 else ""
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "target": round(target),
        "notice": notice,
    }


def estimate_activity_calories(activity_type: str, duration_min: int, weight_kg: float) -> int:
    """A rough MET-based activity estimate, not a food-budget adjustment."""
    met = EXERCISES[activity_type]
    return round(met * weight_kg * (duration_min / 60))


def get_pet_progress(total_xp: int) -> dict[str, Any]:
    for stage_index, (stage_name, start, next_threshold, description) in enumerate(
        PET_STAGES
    ):
        if next_threshold is None or total_xp < next_threshold:
            if next_threshold is None:
                progress = 1.0
                remaining = 0
                next_stage = "Fully grown"
            else:
                progress = min(
                    1.0,
                    max(0.0, (total_xp - start) / (next_threshold - start)),
                )
                remaining = max(0, next_threshold - total_xp)
                next_stage = PET_STAGES[stage_index + 1][0].lower()
            return {
                "stage": stage_name,
                "description": description,
                "progress": progress,
                "remaining": remaining,
                "next_stage": next_stage,
            }
    return {
        "stage": "Adult",
        "description": PET_STAGES[-1][3],
        "progress": 1.0,
        "remaining": 0,
        "next_stage": "Fully grown",
    }


def style_app() -> None:
    """A light pastel theme requested for the student demonstration."""
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 8% 2%, rgba(255, 223, 234, .52), transparent 24rem),
                radial-gradient(circle at 92% 12%, rgba(225, 216, 255, .40), transparent 25rem),
                #fffdf9;
            color: #342b42;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fff3f7 0%, #f5f0ff 100%);
        }
        [data-testid="stMetric"] {
            background: rgba(255,255,255,.88);
            border: 1px solid #f0e5f1;
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: 0 5px 18px rgba(76, 56, 90, .05);
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 14px;
            border: 1px solid #d8c7ef;
            background: #f4edff;
            color: #45375b;
            font-weight: 650;
            min-height: 2.7rem;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
            border-color: #bd9bdd;
            color: #35264b;
            background: #eee3ff;
        }
        [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #efaec4, #b99cdd, #98d5c2);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 20px;
            border-color: #f0e5f1;
            background: rgba(255,255,255,.72);
        }
        h1, h2, h3 { color: #453453; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_calorie_guidance(profile: dict[str, Any]) -> dict[str, Any]:
    estimate = calculate_calories(profile)
    if estimate["notice"] == "adult":
        st.info(
            "Adult calorie formulas are turned off for people under 18. "
            "A clinician can give age-appropriate guidance."
        )
        return estimate
    if estimate["notice"] == "range":
        st.info(
            "This estimate falls outside the app's general-use range, so it "
            "doesn't suggest a calorie target. A registered dietitian can help "
            "with an individual plan."
        )
        if estimate["bmr"] is not None:
            st.caption(
                f"Formula estimates only: BMR {estimate['bmr']:,} kcal · "
                f"TDEE {estimate['tdee']:,} kcal."
            )
        return estimate

    columns = st.columns(3)
    columns[0].metric("Estimated BMR", f"{estimate['bmr']:,} kcal")
    columns[1].metric("Estimated maintenance", f"{estimate['tdee']:,} kcal")
    columns[2].metric("Gentle daily target", f"{estimate['target']:,} kcal")
    if estimate["notice"] == "floor":
        st.info(
            "The app keeps weight-loss estimates at or above 1,500 kcal. "
            "If that is not below your estimated maintenance, it won't suggest "
            "eating less; seek personal guidance instead."
        )
    st.caption(
        "Mifflin–St Jeor is a rough adult estimate. The app uses a 300 kcal "
        "weight-loss adjustment or a 250 kcal weight-gain adjustment. "
        "It is not medical advice."
    )
    return estimate


def render_profile_form(profile: dict[str, Any] | None, total_xp: int = 0) -> None:
    st.subheader("Your profile")
    st.write(
        "These estimates are for adult demonstration use. Your information is "
        "stored only in this app's local SQLite file."
    )
    current = profile or {
        "name": "",
        "age": 18,
        "gender": GENDER_OPTIONS[0],
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "light",
        "health_goal": "maintenance",
        "egg_type": "cat",
    }
    gender_index = GENDER_OPTIONS.index(current["gender"])
    activity_keys = list(ACTIVITY_LEVELS)
    goal_keys = list(GOAL_OPTIONS)
    egg_keys = list(EGG_OPTIONS)

    with st.form("profile_form"):
        name = st.text_input("Name", value=current["name"], max_chars=60)
        first, second = st.columns(2)
        age = first.number_input(
            "Age",
            min_value=13,
            max_value=100,
            value=int(current["age"]),
            step=1,
        )
        gender = second.selectbox(
            "Gender for estimate",
            GENDER_OPTIONS,
            index=gender_index,
            help=(
                "The formula uses a female or male coefficient for those "
                "selections and their midpoint for other / prefer not to say."
            ),
        )
        height_col, weight_col = st.columns(2)
        height_cm = height_col.number_input(
            "Height (cm)",
            min_value=120.0,
            max_value=220.0,
            value=float(current["height_cm"]),
            step=0.5,
        )
        weight_kg = weight_col.number_input(
            "Current weight (kg)",
            min_value=30.0,
            max_value=250.0,
            value=float(current["weight_kg"]),
            step=0.1,
        )
        activity_level = st.selectbox(
            "Activity level",
            activity_keys,
            index=activity_keys.index(current["activity_level"]),
            format_func=lambda key: ACTIVITY_LEVELS[key][0],
        )
        health_goal = st.selectbox(
            "Health goal",
            goal_keys,
            index=goal_keys.index(current["health_goal"]),
            format_func=lambda key: GOAL_OPTIONS[key],
        )
        egg_type = st.selectbox(
            "Choose a mystery egg category",
            egg_keys,
            index=egg_keys.index(current["egg_type"]),
            format_func=lambda key: EGG_OPTIONS[key],
            disabled=total_xp >= 30,
            help="Your pet's appearance stays hidden until the egg hatches.",
        )
        submitted = st.form_submit_button("Save profile")

    if submitted:
        cleaned_name = name.strip()
        if not cleaned_name:
            st.error("Please enter a name.")
            return
        values = {
            "name": cleaned_name,
            "age": int(age),
            "gender": gender,
            "height_cm": float(height_cm),
            "weight_kg": float(weight_kg),
            "activity_level": activity_level,
            "health_goal": health_goal,
            "egg_type": egg_type,
        }
        save_profile(values)
        st.success("Profile saved.")
        st.rerun()


def render_onboarding() -> None:
    st.title("SmartMeal")
    st.subheader("My Little Healthy Pet")
    st.write(
        "Build gentle, everyday habits with a food diary, simple trackers, "
        "and a tiny companion that grows when you care for yourself."
    )
    st.info(
        "Start by creating a profile, or load clearly labeled sample data "
        "for a quick class demonstration."
    )
    render_profile_form(None)
    st.divider()
    st.caption(
        "This is a single-user learning project. It is not a medical tool, "
        "and it does not send your records to a server."
    )
    if st.button("Load sample demo data", key="load_demo"):
        load_demo_profile()
        st.success("Sample profile and example records added.")
        st.rerun()


def render_pet_card(profile: dict[str, Any], total_xp: int) -> None:
    progress = get_pet_progress(total_xp)
    stage = progress["stage"]
    pet_face = "🥚" if stage == "Egg" else PET_FACES[profile["egg_type"]]
    with st.container(border=True):
        left, right = st.columns([1, 3])
        left.markdown(
            f"<div style='font-size:5rem;text-align:center;padding-top:.3rem'>"
            f"{pet_face}</div>",
            unsafe_allow_html=True,
        )
        right.subheader(f"Your pet · {stage}")
        right.write(progress["description"])
        right.metric("Care XP", f"{total_xp} XP")
        if progress["remaining"]:
            right.progress(
                progress["progress"],
                text=f"{progress['remaining']} XP until {progress['next_stage']}",
            )
        else:
            right.progress(1.0, text="Fully grown")
        if stage == "Egg":
            st.caption(
                "The pet's appearance is a surprise until it hatches. "
                "Earn XP by logging meals, water, movement, and your daily check-in."
            )


def render_dashboard(profile: dict[str, Any]) -> None:
    today = date.today()
    today_string = today.isoformat()
    total_xp = get_total_xp()
    summary = get_daily_summary(today_string)
    estimate = calculate_calories(profile)

    st.title(f"Hello, {profile['name']}!")
    st.caption("A gentle snapshot of your day. Every log is information, not a grade.")

    calorie_target = estimate["target"]
    first, second, third = st.columns(3)
    first.metric("Food logged", f"{summary['calories']:,.0f} kcal")
    second.metric(
        "Daily target estimate",
        f"{calorie_target:,.0f} kcal" if calorie_target else "Not shown",
    )
    third.metric("Water", f"{summary['water_ml']:,} ml")

    if calorie_target:
        st.progress(
            min(1.0, summary["calories"] / calorie_target),
            text="Food log compared with your estimate — not a score or limit.",
        )
    else:
        st.caption(
            "A calorie target is hidden because this app avoids generic targets "
            "for minors or estimates outside its general-use range."
        )

    nutrient_cols = st.columns(3)
    nutrient_cols[0].metric("Protein", f"{summary['protein_g']:.0f} g")
    nutrient_cols[1].metric("Carbohydrates", f"{summary['carbs_g']:.0f} g")
    nutrient_cols[2].metric("Fat", f"{summary['fat_g']:.0f} g")

    activity_col, water_col = st.columns(2)
    with activity_col:
        st.metric(
            "Movement",
            f"{summary['activity_min']} min",
            f"~{summary['activity_calories']} activity kcal",
        )
        st.caption(
            "Activity calories are rough estimates and are not subtracted "
            "from your food target."
        )
    with water_col:
        st.metric("Water reminder", f"{WATER_GOAL_ML:,} ml")
        st.progress(
            min(1.0, summary["water_ml"] / WATER_GOAL_ML),
            text=f"{summary['water_ml']:,} / {WATER_GOAL_ML:,} ml logged",
        )
        st.caption(
            "A gentle reminder, not a prescription. Follow medical advice "
            "if you have fluid restrictions."
        )

    pet_col, checkin_col = st.columns([1.3, 1])
    with pet_col:
        render_pet_card(profile, total_xp)
    with checkin_col:
        with st.container(border=True):
            st.subheader("A little care counts")
            st.write(
                "Check in once today to earn 5 XP. No food or exercise goal "
                "is required."
            )
            checked_in = has_daily_checkin(today_string)
            if st.button(
                "Today's gentle check-in",
                disabled=checked_in,
                key="daily_checkin",
            ):
                record_daily_checkin(today_string)
                st.success("Check-in saved. Your pet earned 5 XP.")
                st.rerun()
            if checked_in:
                st.caption("Today's check-in is already saved.")

    st.subheader("Today's food diary")
    meals = list_meals(today_string)
    if meals:
        st.dataframe(
            pd.DataFrame(meals)[
                ["meal_type", "food_name", "servings", "calories", "protein_g"]
            ].rename(
                columns={
                    "meal_type": "Meal",
                    "food_name": "Food",
                    "servings": "Servings",
                    "calories": "kcal",
                    "protein_g": "Protein (g)",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No meals logged today. Add one whenever you're ready.")


def render_meal_diary() -> None:
    st.title("Food diary")
    st.caption(
        "Thai food nutrition values are approximate and vary by recipe and portion."
    )
    custom_food = st.toggle("Enter a custom food")
    with st.form("meal_form"):
        first, second = st.columns(2)
        meal_date = first.date_input("Meal date", value=date.today())
        meal_type = second.selectbox(
            "Meal type", ["Breakfast", "Lunch", "Dinner", "Snack"]
        )

        if custom_food:
            food_name = st.text_input("Food name", max_chars=80)
            calories_col, servings_col = st.columns(2)
            calories = calories_col.number_input(
                "Calories per serving", min_value=0.0, max_value=5000.0, step=10.0
            )
            servings = servings_col.number_input(
                "Servings", min_value=0.25, max_value=8.0, value=1.0, step=0.25
            )
            macro_cols = st.columns(3)
            protein = macro_cols[0].number_input(
                "Protein (g)", min_value=0.0, max_value=300.0, step=1.0
            )
            carbs = macro_cols[1].number_input(
                "Carbohydrates (g)", min_value=0.0, max_value=500.0, step=1.0
            )
            fat = macro_cols[2].number_input(
                "Fat (g)", min_value=0.0, max_value=300.0, step=1.0
            )
        else:
            food_name = st.selectbox("Thai food", list(THAI_FOODS))
            servings = st.number_input(
                "Servings", min_value=0.25, max_value=8.0, value=1.0, step=0.25
            )
            nutrition = THAI_FOODS[food_name]
            calories = nutrition["calories"]
            protein = nutrition["protein"]
            carbs = nutrition["carbs"]
            fat = nutrition["fat"]
            st.caption(
                f"Per serving: about {calories:.0f} kcal · "
                f"{protein:g} g protein · {carbs:g} g carbs · {fat:g} g fat"
            )

        submitted = st.form_submit_button("Add meal")

    if submitted:
        if custom_food and not food_name.strip():
            st.error("Please enter a food name.")
        else:
            xp = add_meal(
                meal_date.isoformat(),
                meal_type,
                food_name.strip(),
                float(servings),
                float(calories) * float(servings),
                float(protein) * float(servings),
                float(carbs) * float(servings),
                float(fat) * float(servings),
            )
            st.success(
                f"Meal saved. {f'+{xp} XP for logging it.' if xp else 'Your daily meal-log XP limit is reached.'}"
            )
            st.rerun()

    st.subheader("Remove a meal")
    diary_day = st.date_input("Show meals for", value=date.today(), key="diary_day")
    meals = list_meals(diary_day.isoformat())
    if meals:
        frame = pd.DataFrame(meals)[
            [
                "meal_type",
                "food_name",
                "servings",
                "calories",
                "protein_g",
                "carbs_g",
                "fat_g",
            ]
        ].rename(
            columns={
                "meal_type": "Meal",
                "food_name": "Food",
                "servings": "Servings",
                "calories": "kcal",
                "protein_g": "Protein (g)",
                "carbs_g": "Carbs (g)",
                "fat_g": "Fat (g)",
            }
        )
        st.dataframe(frame, hide_index=True, width="stretch")
        meal_labels = {
            row["id"]: f"{row['meal_type']} · {row['food_name']} · {row['calories']:.0f} kcal"
            for row in meals
        }
        selected_id = st.selectbox(
            "Choose a meal to delete",
            list(meal_labels),
            format_func=lambda item_id: meal_labels[item_id],
            key="meal_to_delete",
        )
        if st.button("Delete selected meal", key="delete_meal"):
            delete_record("meal", selected_id)
            st.success("Meal deleted.")
            st.rerun()
    else:
        st.info("No meals are saved for this date.")


def render_water_tracker() -> None:
    st.title("Water tracker")
    st.caption(
        "Track what you drink. The 2,000 ml marker is only a general reminder; "
        "follow your clinician's advice if it differs."
    )
    with st.form("water_form"):
        entry_date = st.date_input("Date", value=date.today())
        amount_ml = st.number_input(
            "Water amount (ml)",
            min_value=50,
            max_value=2000,
            value=250,
            step=50,
        )
        submitted = st.form_submit_button("Log water")
    if submitted:
        xp = add_water(entry_date.isoformat(), int(amount_ml))
        st.success(
            f"Water saved. {f'+{xp} XP for logging it.' if xp else 'Your daily water-log XP limit is reached.'}"
        )
        st.rerun()

    selected_day = st.date_input(
        "Review water for", value=date.today(), key="water_review_day"
    )
    entries = list_water_entries(selected_day.isoformat())
    total_ml = sum(row["amount_ml"] for row in entries)
    st.metric("Total logged", f"{total_ml:,} ml")
    st.progress(
        min(1.0, total_ml / WATER_GOAL_ML),
        text=f"{total_ml:,} / {WATER_GOAL_ML:,} ml reminder",
    )
    if entries:
        entry_labels = {
            row["id"]: f"{row['amount_ml']} ml · {row['created_at']}"
            for row in entries
        }
        selected_id = st.selectbox(
            "Choose an entry to delete",
            list(entry_labels),
            format_func=lambda item_id: entry_labels[item_id],
            key="water_to_delete",
        )
        if st.button("Delete selected water entry", key="delete_water"):
            delete_record("water", selected_id)
            st.success("Water entry deleted.")
            st.rerun()
    else:
        st.info("No water entries are saved for this date.")


def render_activity_tracker(profile: dict[str, Any]) -> None:
    st.title("Activity tracker")
    st.caption(
        "Movement is for well-being, not a way to earn food or compensate for meals."
    )
    with st.form("activity_form"):
        first, second = st.columns(2)
        entry_date = first.date_input("Activity date", value=date.today())
        activity_type = second.selectbox("Activity", list(EXERCISES))
        duration_min = st.number_input(
            "Duration (minutes)", min_value=1, max_value=600, value=30, step=5
        )
        submitted = st.form_submit_button("Save activity")

    if submitted:
        burn = estimate_activity_calories(
            activity_type, int(duration_min), float(profile["weight_kg"])
        )
        xp = add_activity(
            entry_date.isoformat(), activity_type, int(duration_min), burn
        )
        st.success(
            f"Activity saved. Estimated burn: about {burn} kcal. "
            f"{f'+{xp} XP for logging it.' if xp else 'Your daily activity-log XP limit is reached.'}"
        )
        st.rerun()

    selected_day = st.date_input(
        "Review activity for", value=date.today(), key="activity_review_day"
    )
    entries = list_activities(selected_day.isoformat())
    if entries:
        st.dataframe(
            pd.DataFrame(entries)[
                ["activity_type", "duration_min", "calories_burned"]
            ].rename(
                columns={
                    "activity_type": "Activity",
                    "duration_min": "Minutes",
                    "calories_burned": "Estimated kcal",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        labels = {
            row["id"]: f"{row['activity_type']} · {row['duration_min']} min"
            for row in entries
        }
        selected_id = st.selectbox(
            "Choose an activity to delete",
            list(labels),
            format_func=lambda item_id: labels[item_id],
            key="activity_to_delete",
        )
        if st.button("Delete selected activity", key="delete_activity"):
            delete_record("activity", selected_id)
            st.success("Activity deleted.")
            st.rerun()
    else:
        st.info("No activities are saved for this date.")
    st.caption(
        "Burn estimates use a simple activity multiplier and your saved weight. "
        "They can be quite different from a person's actual energy use."
    )


def render_weight_tracker() -> None:
    st.title("Weight tracker")
    st.caption(
        "A private history for your own reference. Logging a weight change never "
        "earns or removes pet XP."
    )
    with st.form("weight_form"):
        first, second = st.columns(2)
        entry_date = first.date_input("Measurement date", value=date.today())
        weight_kg = second.number_input(
            "Weight (kg)", min_value=20.0, max_value=300.0, value=60.0, step=0.1
        )
        submitted = st.form_submit_button("Save measurement")
    if submitted:
        add_weight(entry_date.isoformat(), float(weight_kg))
        st.success("Measurement saved.")
        st.rerun()

    weights = list_weights()
    if weights:
        frame = pd.DataFrame(weights)
        frame["entry_date"] = pd.to_datetime(frame["entry_date"])
        frame = frame.sort_values(["entry_date", "id"])
        figure, axis = plt.subplots(figsize=(9, 4))
        axis.plot(
            frame["entry_date"],
            frame["weight_kg"],
            color="#a678c5",
            marker="o",
            linewidth=2.5,
            markersize=7,
        )
        axis.set_title("Your recorded weight history")
        axis.set_ylabel("Weight (kg)")
        axis.set_xlabel("Date")
        axis.grid(alpha=0.2)
        figure.autofmt_xdate()
        figure.tight_layout()
        st.pyplot(figure, clear_figure=True)
        plt.close(figure)

        display = frame.assign(
            entry_date=frame["entry_date"].dt.strftime("%Y-%m-%d")
        )[["id", "entry_date", "weight_kg"]].rename(
            columns={
                "entry_date": "Date",
                "weight_kg": "Weight (kg)",
            }
        )
        st.dataframe(display.drop(columns=["id"]), hide_index=True, width="stretch")
        labels = {
            row["id"]: f"{row['entry_date']} · {row['weight_kg']:.1f} kg"
            for row in weights
        }
        selected_id = st.selectbox(
            "Choose a measurement to delete",
            list(labels),
            format_func=lambda item_id: labels[item_id],
            key="weight_to_delete",
        )
        if st.button("Delete selected measurement", key="delete_weight"):
            delete_record("weight", selected_id)
            st.success("Measurement deleted.")
            st.rerun()
    else:
        st.info("No weight measurements saved yet.")


def render_pet_page(profile: dict[str, Any]) -> None:
    st.title("My little healthy pet")
    total_xp = get_total_xp()
    render_pet_card(profile, total_xp)
    st.subheader("How your pet grows")
    for stage, start, next_threshold, description in PET_STAGES:
        if next_threshold is None:
            requirement = f"{start}+ XP"
        else:
            requirement = f"{start}–{next_threshold - 1} XP"
        st.write(f"**{stage} · {requirement}** — {description}")
    st.info(
        "XP comes from logging meals, water, movement, and one gentle daily "
        "check-in. There are daily caps. Skipping food, calorie deficits, "
        "and weight changes never earn XP."
    )


def render_profile_page(profile: dict[str, Any]) -> None:
    st.title("Profile and calorie estimate")
    render_profile_form(profile, get_total_xp())
    st.divider()
    st.subheader("Your estimate")
    show_calorie_guidance(profile)
    st.caption(
        "The BMR formula uses the coefficient matching the selected gender "
        "or a midpoint for other / prefer not to say. Estimates are imperfect "
        "and are not a diagnosis or treatment plan."
    )
    st.divider()
    st.caption(
        "SmartMeal is a local, single-user university demo. Your profile and "
        "logs are stored in smartmeal.db on this computer. Don't commit that "
        "database or publish personal health information."
    )


def main() -> None:
    st.set_page_config(
        page_title="SmartMeal – My Little Healthy Pet",
        page_icon="🥚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    initialize_database()
    style_app()
    profile = get_profile()

    if profile is None:
        render_onboarding()
        return

    with st.sidebar:
        st.markdown("## SmartMeal")
        st.caption("My Little Healthy Pet")
        page = st.radio(
            "Your space",
            [
                "Dashboard",
                "Food diary",
                "Water tracker",
                "Activity tracker",
                "Weight tracker",
                "My pet",
                "Profile & settings",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Your records stay in the local SQLite database.")

    if page == "Dashboard":
        render_dashboard(profile)
    elif page == "Food diary":
        render_meal_diary()
    elif page == "Water tracker":
        render_water_tracker()
    elif page == "Activity tracker":
        render_activity_tracker(profile)
    elif page == "Weight tracker":
        render_weight_tracker()
    elif page == "My pet":
        render_pet_page(profile)
    else:
        render_profile_page(profile)


if __name__ == "__main__":
    main()
