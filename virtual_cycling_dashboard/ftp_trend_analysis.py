import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the CSV
df = pd.read_csv("strava_virtual_summary.csv")

# Convert start_date to datetime
df['start_date'] = pd.to_datetime(df['start_date'])

# Sort by date
df = df.sort_values('start_date')

# Calculate W/kg if not already in CSV
weight_kg = 53  # replace with your weight
df['w_per_kg'] = df['average_power'] / weight_kg

# Create figure and primary axis
fig, ax1 = plt.subplots(figsize=(12,6))

# Plot W/kg on primary y-axis
sns.lineplot(data=df, x='start_date', y='w_per_kg', marker='o', ax=ax1, label='W/kg', color='blue')
ax1.set_xlabel("Date")
ax1.set_ylabel("Average Power-to-Weight (W/kg)", color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Create secondary y-axis for heart rate
ax2 = ax1.twinx()
sns.lineplot(data=df, x='start_date', y='average_hr', marker='s', ax=ax2, label='Average HR', color='red')
ax2.set_ylabel("Average Heart Rate (bpm)", color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Title and layout
plt.title("Performance and Heart Rate Trend for Virtual Rides 2025")
fig.autofmt_xdate()
plt.grid(True)
fig.tight_layout()

# Show plot
plt.show()

# Optional: Save figure
fig.savefig("wkg_hr_trend_2025.png")
