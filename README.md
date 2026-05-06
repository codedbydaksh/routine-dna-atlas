<p align="center">
  <img src="Banner.png" alt="Routine DNA Atlas Banner"/>
</p>

<h1 align="center">Routine DNA Atlas</h1>

<p align="center">
Behavior Analytics • Productivity Intelligence • Focus Tracking
</p>

Routine DNA Atlas is a Python-powered routine intelligence dashboard that turns daily activity logs into structured insights. It helps users understand how their time is distributed, where focus is strongest, where distraction appears, and how consistent their routine really is.

Built with **Streamlit**, **Pandas**, **NumPy**, and **Matplotlib**, the project transforms a simple CSV file into a visual productivity profile with scoring, trend analysis, anomaly detection, and actionable recommendations.

---

## What the Project Does

Routine DNA Atlas reads routine data from a CSV file and performs a full analysis pipeline:

- calculates time spent on each activity category
- measures daily productivity trends
- builds a custom focus score
- detects unusual routine days
- evaluates consistency across days
- generates visual dashboards and downloadable summaries

The goal is not just to display data, but to interpret behavior.

---

## Why This Project Stands Out

Most routine trackers only store logs.  
This project goes further by turning logs into a **behavioral fingerprint**.

It combines:
- **analysis**
- **visualization**
- **scoring**
- **classification**
- **recommendation logic**

That makes it useful for students, self-trackers, productivity enthusiasts, and anyone who wants to understand their daily rhythm more deeply.

---

## Feature Walkthrough

Routine DNA Atlas is structured as an end-to-end routine intelligence system. Each section of the dashboard represents a different layer of analysis, moving from raw input to actionable insight.

### 1. Dashboard Overview
The dashboard opens with a high-level summary of the routine dataset. It surfaces the most important metrics immediately, including total days logged, total hours tracked, top category by time, and overall consistency. This gives the user an instant read on routine quality without needing to inspect the raw data first.

### 2. Controls Panel
The controls panel turns the dashboard into an interactive analysis tool. Users can filter the dataset by date range, category, activity, energy level, and mood, while also tuning the scoring weights for deep work, rest, phone usage, exercise, and sleep. This makes the analysis adaptive rather than fixed.

### 3. Data Preview
The data preview section shows the filtered dataset after validation and cleaning. It helps confirm that the uploaded CSV has been parsed correctly and that the analysis is being performed on structured, reliable data. This section is especially useful for verifying input quality before interpreting results.

### 4. Metrics Overview
The metrics section summarizes the core quantitative signals behind the routine. It visualizes category-wise time distribution and daily activity volume, making it easier to identify imbalance, overloading, or underutilized time blocks. This layer acts as the numerical foundation of the dashboard.

### 5. Productivity Trends
The trends section focuses on how routine behavior changes over time. It visualizes the focus score and consistency score across days, helping users identify productive streaks, unstable periods, and shifts in daily rhythm. This is the section that reveals whether performance is steady or fluctuating.

### 6. Productivity Intelligence
This section represents the analytical core of the project. It combines the custom productivity score, routine classification, and heatmap visualization to transform raw logs into a behavioral interpretation. Instead of only reporting activity, it helps define the shape of the user’s routine.

### 7. Recommendations and Anomaly Detection
This part of the dashboard detects unusual patterns using anomaly logic and generates practical recommendations based on observed behavior. It can highlight overuse of phone time, low deep-work duration, routine instability, or other signals that may affect productivity. The goal is not just to observe behavior, but to improve it.

### 8. Exported Tables
The export section presents computed summaries in a structured tabular format. It includes category summaries, daily hours, focus scores, and daily consistency scores, making the results easy to reuse, download, or reference in further analysis.

## How the Dashboard Works

The system follows a clear analytical pipeline:

**Upload Data → Validate & Clean → Filter → Score → Detect Patterns → Generate Insights → Export Results**

This flow makes Routine DNA Atlas feel like a real analytics product rather than a standalone script.

---

## Tech Stack

- **Python**
- **Streamlit**
- **Pandas**
- **NumPy**
- **Matplotlib**

---

## Project Structure

```text
routine-dna-atlas/
├── app.py
├── analysis.py
├── requirements.txt
├── .gitignore
├── data/
│   └── routine_log.csv
└── README.md
