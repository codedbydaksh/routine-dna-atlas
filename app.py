import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ==================================================
# ROUTINE DNA ATLAS
# Streamlit dashboard with:
# - validation
# - custom scoring
# - filters
# - productivity score
# - profile classification
# - heatmap
# - transition matrix
# - anomaly detection
# - recommendations
# - CSV export
# ==================================================

st.set_page_config(
    page_title="Routine DNA Atlas",
    page_icon="📊",
    layout="wide",
)

st.title("Routine DNA Atlas")
st.caption("Behavior analytics dashboard for your daily routine")

# ------------------------------
# Configuration
# ------------------------------
REQUIRED_COLUMNS = [
    "date",
    "start_time",
    "end_time",
    "activity",
    "category",
    "energy",
    "mood",
    "location",
    "notes",
]


# ------------------------------
# Helper functions
# ------------------------------
def validate_columns(df: pd.DataFrame):
    present = set(df.columns)
    required = set(REQUIRED_COLUMNS)
    missing = sorted(list(required - present))
    extra = sorted(list(present - required))
    return missing, extra


def parse_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")

    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["activity", "category", "location", "notes"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "energy" in df.columns:
        df["energy"] = pd.to_numeric(df["energy"], errors="coerce")
    if "mood" in df.columns:
        df["mood"] = pd.to_numeric(df["mood"], errors="coerce")

    df = df.drop_duplicates()
    df = df.dropna(subset=["date", "start_time", "end_time", "category"])

    df["duration"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60
    df = df[df["duration"].notna()]
    df = df[df["duration"] >= 0]

    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["weekday"] = pd.to_datetime(df["date"]).dt.day_name()
    df["hour"] = df["start_time"].dt.hour
    df["week"] = pd.to_datetime(df["date"]).dt.isocalendar().week.astype(int)
    return df


def compute_category_time(df: pd.DataFrame) -> pd.Series:
    return df.groupby("category")["duration"].sum().sort_values(ascending=False)


def compute_daily_time(df: pd.DataFrame) -> pd.Series:
    return df.groupby("date")["duration"].sum().sort_index()


def compute_focus_score(
    df: pd.DataFrame,
    deep_weight: float,
    rest_penalty: float,
    phone_penalty: float,
    exercise_bonus: float,
    sleep_bonus: float,
) -> pd.Series:
    daily_index = compute_daily_time(df).index

    deep = (
        df[df["category"] == "Deep Work"]
        .groupby("date")["duration"]
        .sum()
        .reindex(daily_index, fill_value=0)
    )
    rest = (
        df[df["category"] == "Rest"]
        .groupby("date")["duration"]
        .sum()
        .reindex(daily_index, fill_value=0)
    )
    phone = (
        df[df["activity"].astype(str).str.contains("Phone", case=False, na=False)]
        .groupby("date")["duration"]
        .sum()
        .reindex(daily_index, fill_value=0)
    )
    exercise = (
        df[df["category"] == "Health"]
        .groupby("date")["duration"]
        .sum()
        .reindex(daily_index, fill_value=0)
    )
    sleep = (
        df[df["activity"].astype(str).str.contains("Sleep", case=False, na=False)]
        .groupby("date")["duration"]
        .sum()
        .reindex(daily_index, fill_value=0)
    )

    focus = (
        (deep * deep_weight)
        - (rest * rest_penalty)
        - (phone * phone_penalty)
        + (exercise * exercise_bonus)
        + (sleep * sleep_bonus)
    )

    return focus.fillna(0)


def compute_consistency_score(daily_time_hours: pd.Series) -> tuple[float, pd.Series]:
    mean_hours = daily_time_hours.mean()
    std_hours = daily_time_hours.std()

    if pd.isna(mean_hours) or mean_hours == 0:
        consistency = 0.0
        daily_consistency = daily_time_hours * 0
    else:
        consistency = max(0.0, 100 - (std_hours / mean_hours) * 100)
        daily_consistency = 100 - (abs(daily_time_hours - mean_hours) / mean_hours) * 100
        daily_consistency = daily_consistency.clip(lower=0)

    return consistency, daily_consistency


def detect_anomalies(focus_score: pd.Series, daily_time_hours: pd.Series) -> pd.DataFrame:
    summary = pd.DataFrame(
        {
            "daily_hours": daily_time_hours,
            "focus_score": focus_score,
        }
    ).fillna(0)

    def iqr_flags(s: pd.Series):
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return (s < lower) | (s > upper)

    summary["hours_anomaly"] = iqr_flags(summary["daily_hours"])
    summary["focus_anomaly"] = iqr_flags(summary["focus_score"])
    summary["anomaly"] = summary["hours_anomaly"] | summary["focus_anomaly"]
    return summary


def build_transition_matrix(df: pd.DataFrame) -> pd.DataFrame:
    ordered = df.sort_values(["date", "start_time"]).copy()
    ordered["next_activity"] = ordered["activity"].shift(-1)
    ordered["same_day"] = pd.to_datetime(ordered["date"]) == pd.to_datetime(ordered["date"]).shift(-1)

    transitions = ordered[ordered["same_day"]].dropna(subset=["next_activity"])
    return pd.crosstab(transitions["activity"], transitions["next_activity"])


def build_hour_weekday_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    pivot = pd.pivot_table(
        df,
        values="duration",
        index="weekday",
        columns="hour",
        aggfunc="sum",
        fill_value=0,
    )

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    pivot = pivot.reindex([d for d in weekday_order if d in pivot.index])
    return pivot


def generate_recommendations(
    df: pd.DataFrame,
    focus_score: pd.Series,
    daily_time_hours: pd.Series,
) -> list[str]:
    recs = []

    if not focus_score.empty:
        best_day = focus_score.idxmax()
        worst_day = focus_score.idxmin()
        recs.append(f"Best focus day: {best_day}. Try to replicate that routine pattern.")
        recs.append(f"Worst focus day: {worst_day}. Inspect what changed on that day.")

    category_time = compute_category_time(df)
    top_category = category_time.idxmax() if not category_time.empty else None
    if top_category:
        recs.append(f"Most time goes to '{top_category}'. Decide if that is intentional or a leak.")

    phone_time = df[df["activity"].astype(str).str.contains("Phone", case=False, na=False)]["duration"].sum()
    if phone_time > 120:
        recs.append("Phone usage is high. Add a focused no-phone block during deep work hours.")

    deep_work_time = df[df["category"] == "Deep Work"]["duration"].sum()
    if deep_work_time < 180:
        recs.append("Deep Work total is low. Try scheduling one protected 90-minute focus block daily.")

    if daily_time_hours.mean() < 3:
        recs.append("Logged study/work time is low. Add more entries or log the full day for better accuracy.")

    return recs[:6]


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def show_summary_cards(
    df: pd.DataFrame,
    category_time: pd.Series,
    daily_time_hours: pd.Series,
    consistency_score: float,
):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Days", int(df["date"].nunique()))
    c2.metric("Total Hours", round(float(daily_time_hours.sum()), 2))
    c3.metric("Top Category", str(category_time.idxmax()) if not category_time.empty else "N/A")
    c4.metric("Consistency", f"{round(consistency_score, 2)}")


def plot_heatmap(heatmap_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(14, 5))
    im = ax.imshow(heatmap_df.values, aspect="auto", cmap="Blues")

    ax.set_xticks(range(len(heatmap_df.columns)))
    ax.set_xticklabels(heatmap_df.columns)
    ax.set_yticks(range(len(heatmap_df.index)))
    ax.set_yticklabels(heatmap_df.index)
    ax.set_title("Weekday vs Hour Heatmap (Duration)")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Weekday")

    fig.colorbar(im, ax=ax, label="Minutes")
    st.pyplot(fig)


# ------------------------------
# Sidebar controls
# ------------------------------
st.sidebar.header("Controls")
st.sidebar.caption("Use these controls to tune the analysis.")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

st.sidebar.subheader("Scoring Weights")
deep_weight = st.sidebar.slider("Deep Work weight", 0.5, 3.0, 1.0, 0.1)
rest_penalty = st.sidebar.slider("Rest penalty", 0.0, 2.0, 0.5, 0.1)
phone_penalty = st.sidebar.slider("Phone penalty", 0.0, 3.0, 1.0, 0.1)
exercise_bonus = st.sidebar.slider("Exercise bonus", 0.0, 3.0, 0.5, 0.1)
sleep_bonus = st.sidebar.slider("Sleep bonus", 0.0, 3.0, 0.2, 0.1)

show_heatmap = st.sidebar.checkbox("Show heatmap", value=True)
show_transition_matrix = st.sidebar.checkbox("Show transition matrix", value=True)
show_anomalies = st.sidebar.checkbox("Show anomalies", value=True)
show_recommendations = st.sidebar.checkbox("Show recommendations", value=True)

# ------------------------------
# Main app
# ------------------------------
if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)

        missing_cols, extra_cols = validate_columns(raw_df)
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
            st.stop()
        if extra_cols:
            st.sidebar.warning(f"Extra columns detected: {extra_cols}")

        df = parse_datetime_columns(raw_df)
        df = clean_data(df)
        df = add_time_features(df)

        if df.empty:
            st.error("No valid rows remain after cleaning. Check your CSV data.")
            st.stop()

        st.sidebar.subheader("Filters")
        min_date = pd.to_datetime(df["date"]).min().date()
        max_date = pd.to_datetime(df["date"]).max().date()

        date_range = st.sidebar.date_input(
            "Select date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        categories = sorted(df["category"].dropna().unique().tolist())
        selected_categories = st.sidebar.multiselect(
            "Select categories",
            categories,
            default=categories,
        )

        activities = sorted(df["activity"].dropna().unique().tolist())
        selected_activities = st.sidebar.multiselect(
            "Select activities",
            activities,
            default=activities,
        )

        energy_min = float(np.nanmin(df["energy"])) if "energy" in df.columns and df["energy"].notna().any() else 0.0
        energy_max = float(np.nanmax(df["energy"])) if "energy" in df.columns and df["energy"].notna().any() else 10.0
        mood_min = float(np.nanmin(df["mood"])) if "mood" in df.columns and df["mood"].notna().any() else 0.0
        mood_max = float(np.nanmax(df["mood"])) if "mood" in df.columns and df["mood"].notna().any() else 10.0

        energy_range = st.sidebar.slider("Energy range", energy_min, energy_max, (energy_min, energy_max))
        mood_range = st.sidebar.slider("Mood range", mood_min, mood_max, (mood_min, mood_max))

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date

        filtered_df = df[
            (pd.to_datetime(df["date"]).dt.date >= start_date)
            & (pd.to_datetime(df["date"]).dt.date <= end_date)
            & (df["category"].isin(selected_categories))
            & (df["activity"].isin(selected_activities))
        ].copy()

        if "energy" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["energy"].between(energy_range[0], energy_range[1], inclusive="both")
                | filtered_df["energy"].isna()
            ]
        if "mood" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["mood"].between(mood_range[0], mood_range[1], inclusive="both")
                | filtered_df["mood"].isna()
            ]

        if filtered_df.empty:
            st.warning("No rows match the current filters.")
            st.stop()

        category_time = compute_category_time(filtered_df)
        daily_time = compute_daily_time(filtered_df)
        daily_time_hours = daily_time / 60
        focus_score = compute_focus_score(
            filtered_df,
            deep_weight=deep_weight,
            rest_penalty=rest_penalty,
            phone_penalty=phone_penalty,
            exercise_bonus=exercise_bonus,
            sleep_bonus=sleep_bonus,
        )
        consistency_score, daily_consistency = compute_consistency_score(daily_time_hours)

        # extra wow features
        productivity_score = (
            filtered_df[filtered_df["category"] == "Deep Work"]["duration"].sum()
            + filtered_df[filtered_df["category"] == "Health"]["duration"].sum()
            + filtered_df[filtered_df["activity"].astype(str).str.contains("Sleep", case=False, na=False)]["duration"].sum()
            - (filtered_df[filtered_df["category"] == "Rest"]["duration"].sum() * 0.5)
            - (filtered_df[filtered_df["activity"].astype(str).str.contains("Phone", case=False, na=False)]["duration"].sum() * 1.2)
        )

        if not focus_score.empty:
            best_day = focus_score.idxmax()
            worst_day = focus_score.idxmin()
        else:
            best_day = "N/A"
            worst_day = "N/A"

        show_summary_cards(filtered_df, category_time, daily_time_hours, consistency_score)

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["Filtered Data", "Insights", "Downloads"])

        with tab1:
            st.subheader("Filtered Data Preview")
            st.dataframe(filtered_df, use_container_width=True)

        with tab2:
            left, right = st.columns(2)
            with left:
                st.markdown("### Time per Category")
                st.bar_chart(category_time)
            with right:
                st.markdown("### Daily Time Trend (Hours)")
                st.line_chart(daily_time_hours)

            st.markdown("### Focus Score Trend")
            st.line_chart(focus_score)

            st.markdown("### Daily Consistency Trend")
            st.line_chart(daily_consistency)

            st.markdown("### 🚀 Productivity Score")
            st.metric("Score", round(productivity_score, 2))

            st.markdown("### 🧬 Your Routine Type")
            phone_time = filtered_df[filtered_df["activity"].astype(str).str.contains("Phone", case=False, na=False)]["duration"].sum()
            deep_work_time = filtered_df[filtered_df["category"] == "Deep Work"]["duration"].sum()
            rest_time = filtered_df[filtered_df["category"] == "Rest"]["duration"].sum()

            if deep_work_time > phone_time and deep_work_time > rest_time:
                profile = "Deep Worker 🔥"
            elif phone_time > deep_work_time:
                profile = "Distracted Explorer 📱"
            elif rest_time > deep_work_time:
                profile = "Recovery Mode 😴"
            else:
                profile = "Balanced Performer ⚖️"

            st.success(f"Your Profile: {profile}")

            st.markdown("### 🧠 AI Insights")
            insights = []

            if phone_time > 120:
                insights.append("High phone usage detected. It may be affecting productivity.")
            if deep_work_time > rest_time:
                insights.append("You are spending more time in Deep Work. Good sign!")
            if daily_time_hours.mean() < 3:
                insights.append("Your productive hours are low. Try increasing focused work time.")
            if consistency_score > 80:
                insights.append("Your routine is very consistent. Great discipline!")

            if insights:
                for i in insights:
                    st.write(f"• {i}")
            else:
                st.info("No insights generated yet. Add more data.")

            if show_heatmap:
                st.markdown("### ⏰ Productivity Heatmap")
                heatmap_df = build_hour_weekday_heatmap(filtered_df)
                if not heatmap_df.empty:
                    plot_heatmap(heatmap_df)
                else:
                    st.info("Not enough data to build heatmap yet.")

            if show_transition_matrix:
                st.markdown("### 🔁 Activity Transition Matrix")
                tm = build_transition_matrix(filtered_df)
                if not tm.empty:
                    st.dataframe(tm, use_container_width=True)
                else:
                    st.info("Not enough sequential data to build transition matrix yet.")

            if show_anomalies:
                st.markdown("### ⚠️ Anomaly Detection")
                anomaly_df = detect_anomalies(focus_score, daily_time_hours)
                anomalies = anomaly_df[anomaly_df["anomaly"]]
                if not anomalies.empty:
                    st.warning("Unusual productivity days detected:")
                    st.dataframe(anomalies, use_container_width=True)
                else:
                    st.success("No anomalies detected")

            if show_recommendations:
                st.markdown("### 💡 Recommendations")
                recs = generate_recommendations(filtered_df, focus_score, daily_time_hours)
                if recs:
                    for r in recs:
                        st.write(f"- {r}")
                else:
                    st.info("No recommendations generated yet. Add more data.")

            st.markdown("### Quick Insights")
            a, b, c = st.columns(3)
            a.info(f"Best day by focus: {best_day}")
            b.warning(f"Worst day by focus: {worst_day}")
            c.success(f"Most time spent on: {category_time.idxmax() if not category_time.empty else 'N/A'}")

        with tab3:
            st.subheader("Download Cleaned Data")
            cleaned_csv = dataframe_to_csv_bytes(filtered_df)
            st.download_button(
                label="Download cleaned CSV",
                data=cleaned_csv,
                file_name="cleaned_routine_log.csv",
                mime="text/csv",
            )

            st.subheader("Exported Tables")
            st.write("Category summary")
            st.dataframe(category_time.reset_index(name="duration_minutes"), use_container_width=True)
            st.write("Daily hours")
            st.dataframe(daily_time_hours.reset_index(name="hours"), use_container_width=True)
            st.write("Focus score")
            st.dataframe(focus_score.reset_index(name="focus_score"), use_container_width=True)
            st.write("Daily consistency")
            st.dataframe(daily_consistency.reset_index(name="consistency_score"), use_container_width=True)

        st.markdown("---")
        st.subheader("Summary")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Rows", len(filtered_df))
        s2.metric("Total Days", filtered_df["date"].nunique())
        s3.metric("Total Hours", round(filtered_df["duration"].sum() / 60, 2))
        s4.metric("Consistency", round(consistency_score, 2))

        os.makedirs("output", exist_ok=True)
        filtered_df.to_csv("output/cleaned_log.csv", index=False)
        category_time.to_csv("output/category_summary.csv")
        daily_time_hours.to_csv("output/daily_hours.csv")
        focus_score.to_csv("output/focus_score.csv")
        daily_consistency.to_csv("output/daily_consistency.csv")

        st.success("Outputs saved to the output/ folder.")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
        st.stop()

else:
    st.info("Upload a CSV file to start analyzing your routine.")
    st.markdown(
        """
        ### Expected CSV columns
        date, start_time, end_time, activity, category, energy, mood, location, notes

        ### Example row
        2025-05-05,07:00,08:30,Study,Deep Work,8,7,Home,Math revision
        """
    )