import pandas as pd
import json

# Load dataset
data = pd.read_excel("smart_campus_200_row_dataset.xlsx")

# Total electricity per building
electricity_per_building = data.groupby("Building")["Electricity_Units"].sum().to_dict()

# Calculate utilization
data["Utilization_Percentage"] = (data["Rooms_Used"] / data["Total_Rooms"]) * 100

avg_utilization = data.groupby("Building")["Utilization_Percentage"].mean().round(2).to_dict()

# Highest electricity usage building
highest_usage_building = max(electricity_per_building, key=electricity_per_building.get)

# JSON output
result = {
    "total_electricity_per_building": electricity_per_building,
    "average_utilization_percentage": avg_utilization,
    "highest_usage_building": highest_usage_building
}

print(json.dumps(result, indent=4)) 