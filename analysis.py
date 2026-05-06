import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------
# ROUTINE DNA ATLAS
# This script:
# 1) loads your routine CSV
# 2) converts time columns
# 3) calculates activity duration
# 4) groups data by category and date
# 5) creates custom scores
# 6) saves cleaned output files
# --------------------------------------------------

# --------------------------------------------------
# STEP 1: Load the dataset
# --------------------------------------------------
df = pd.read_csv("data/routine_log.csv")

print("\nData loaded successfully.\n")

# --------------------------------------------------
# STEP 2: Make sure the output folder exists
# --------------------------------------------------
# If the folder does not exist, create it so saving files will not fail.
os.makedirs("output", exist_ok=True)

# --------------------------------------------------
# STEP 3: Convert columns into proper datetime format
# --------------------------------------------------
# This helps pandas understand times as real time values,
# not just plain text.
df["start_time"] = pd.to_datetime(df["start_time"])
df["end_time"] = pd.to_datetime(df["end_time"])

# Optional but useful:
# If you want proper date sorting and date-based analysis,
# convert the date column too.
df["date"] = pd.to_datetime(df["date"])

# --------------------------------------------------
# STEP 4: Show the columns in the dataset
# --------------------------------------------------
print("\nThe columns are:\n")
print(df.columns)
print("\n")

# --------------------------------------------------
# STEP 5: Calculate duration of each activity
# --------------------------------------------------
# end_time - start_time gives a time difference.
# .dt.total_seconds() converts that difference into seconds.
# / 60 converts seconds into minutes.
df["duration"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60

# --------------------------------------------------
# STEP 6: Display the full dataframe with the new duration column
# --------------------------------------------------
print(df)

# --------------------------------------------------
# STEP 7: Group data by category
# --------------------------------------------------
# This tells us how much total time was spent in each category.
# Example:
# Deep Work -> 180 minutes
# Rest -> 45 minutes
category_time = df.groupby("category")["duration"].sum()

print("\nTotal time spent per category:\n")
print(category_time)

# --------------------------------------------------
# STEP 8: Bar chart for category-wise time
# --------------------------------------------------
# This chart is useful because it shows which category dominates your day.

category_time.plot(kind="bar", color="skyblue", width=0.25)

plt.title("Time Spent per Category")
plt.xlabel("Category")
plt.ylabel("Minutes")
plt.xticks(rotation=0)

plt.tight_layout()
# plt.savefig("output/category_time.png")
plt.show()

# --------------------------------------------------
# STEP 9: Group data by date
# --------------------------------------------------
# This gives total active/logged time per day.
daily_time = df.groupby("date")["duration"].sum()

print("\nTotal time per day:\n")
print(daily_time)

# --------------------------------------------------
# STEP 10: Convert daily time from minutes to hours
# --------------------------------------------------
daily_time_hours = daily_time / 60

print("\nTotal hours per day:\n")
print(daily_time_hours)

# --------------------------------------------------
# STEP 11: Line chart for daily time trend
# --------------------------------------------------
# This is better than a bar chart for showing trend over time.

daily_time_hours.plot(kind="line", marker="o", color="coral")

plt.title("Daily Time Trend")
plt.xlabel("Date")
plt.ylabel("Hours")
plt.xticks(rotation=0)
plt.tight_layout()

# plt.savefig("output/daily_trend.png")
plt.show()

# --------------------------------------------------
# STEP 12: Find the most productive and least productive day
# --------------------------------------------------
# idxmax() gives the date where daily_time_hours is highest.
# idxmin() gives the date where daily_time_hours is lowest.
print("\nMost productive day:")
print(daily_time_hours.idxmax())

print("\nLeast productive day:")
print(daily_time_hours.idxmin())

# --------------------------------------------------
# STEP 13: Calculate Deep Work time per day
# --------------------------------------------------
# Filter rows where category is exactly "Deep Work",
# then group by date and sum duration.
deep_work = df[df["category"] == "Deep Work"].groupby("date")["duration"].sum()

# --------------------------------------------------
# STEP 14: Calculate Rest time per day
# --------------------------------------------------
# Filter rows where category is exactly "Rest",
# then group by date and sum duration.
rest_time = df[df["category"] == "Rest"].groupby("date")["duration"].sum()

# --------------------------------------------------
# STEP 15: Replace missing values with 0
# --------------------------------------------------
# If a particular day has no Deep Work or no Rest, pandas returns NaN.
# fillna(0) means "treat missing value as zero time".
deep_work = deep_work.fillna(0)
rest_time = rest_time.fillna(0)

# --------------------------------------------------
# STEP 16: Build a custom Focus Score
# --------------------------------------------------
# Your current formula:
# Focus Score = Deep Work - 0.5 * Rest
#
# This means:
# - more Deep Work increases the score
# - more Rest lowers the score a bit
focus_score = deep_work - (rest_time * 0.5)

# If any missing values still exist, replace them with 0
focus_score = focus_score.fillna(0)

print("\nFocus Score per day:\n")
print(focus_score)

# --------------------------------------------------
# STEP 17: Plot Focus Score trend
# --------------------------------------------------
focus_score.plot(kind="line", marker="o", color="green")

plt.title("Focus Score Trend")
plt.xlabel("Date")
plt.ylabel("Focus Score")
plt.xticks(rotation=0)
plt.tight_layout()


# plt.savefig("output/focus_score.png")
plt.show()

# --------------------------------------------------
# STEP 18: Best and worst day based on Focus Score
# --------------------------------------------------
print("\nBest day:")
print(focus_score.idxmax())

print("\nWorst day:")
print(focus_score.idxmin())

# --------------------------------------------------
# STEP 19: Calculate overall consistency score
# --------------------------------------------------
# Mean tells average logged hours per day.
# Standard deviation tells how much the daily hours change.
mean_hours = daily_time_hours.mean()
std_hours = daily_time_hours.std()

# Avoid divide-by-zero errors if mean_hours is 0 or invalid.
if mean_hours == 0 or np.isnan(mean_hours):
    consistency_score = 0
else:
    # A smaller standard deviation means a more stable routine.
    # So we subtract the relative variation from 100.
    consistency_score = max(0, 100 - (std_hours / mean_hours) * 100)

print("\nConsistency Score (0-100):")
print(round(consistency_score, 2))

# --------------------------------------------------
# STEP 20: Daily consistency score
# --------------------------------------------------
# This tells how close each day is to your average day.
# The closer a day's hours are to the mean, the better the consistency.
daily_consistency = 100 - (abs(daily_time_hours - mean_hours) / mean_hours) * 100

# No negative scores allowed
daily_consistency = daily_consistency.clip(lower=0)

print("\nDaily Consistency:\n")
print(daily_consistency)

# --------------------------------------------------
# STEP 21: Plot daily consistency trend
# --------------------------------------------------
daily_consistency.plot(kind="line", marker="o", color="purple")

plt.title("Daily Consistency Trend")
plt.xlabel("Date")
plt.ylabel("Consistency (0-100)")
plt.xticks(rotation=0)
plt.tight_layout()


# plt.savefig("output/consistency.png")
plt.show()

# --------------------------------------------------
# STEP 22: Final summary printout
# --------------------------------------------------
print("\n===== ROUTINE DNA SUMMARY =====")

print("\nTotal days logged:", df["date"].nunique())

print("\nTop category (by time):")
print(category_time.idxmax())

print("\nTotal hours:")
print(round(daily_time_hours.sum(), 2))

print("\nBest day (Focus):")
print(focus_score.idxmax())

print("\nWorst day (Focus):")
print(focus_score.idxmin())

print("\nConsistency Score:")
print(round(consistency_score, 2))

# --------------------------------------------------
# STEP 23: Save cleaned data and summary files
# --------------------------------------------------
# Cleaned version of your main dataset
df.to_csv("output/cleaned_log.csv", index=False)

# Summary files for later analysis
# category_time.to_csv("output/category_summary.csv")
# daily_time_hours.to_csv("output/daily_hours.csv")
# focus_score.to_csv("output/focus_score.csv")
# daily_consistency.to_csv("output/daily_consistency.csv")