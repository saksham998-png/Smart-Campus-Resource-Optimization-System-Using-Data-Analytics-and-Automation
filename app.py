from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pandas as pd

app = Flask(__name__)
app.secret_key = "smartcampus2025"

# Load dataset
data = pd.read_excel("smart_campus_200_row_dataset.xlsx")

# ── Analysis ──────────────────────────────────────────────
electricity_per_building = data.groupby("Building")["Electricity_Units"].sum().to_dict()
water_per_building = data.groupby("Building")["Water_Usage_Liters"].sum().to_dict()

# Electricity specific analytics
total_electricity = int(data["Electricity_Units"].sum())
avg_electricity = float(round(data["Electricity_Units"].mean(), 2))

highest_elec_building = max(electricity_per_building, key=electricity_per_building.get)
lowest_elec_building = min(electricity_per_building, key=electricity_per_building.get)

# Daily electricity trend
daily_electricity = data.groupby("Date")["Electricity_Units"].sum().to_dict()


data["Utilization_Percentage"] = (data["Rooms_Used"] / data["Total_Rooms"]) * 100
avg_utilization = data.groupby("Building")["Utilization_Percentage"].mean().round(2).to_dict()

highest_elec_building = max(electricity_per_building, key=electricity_per_building.get)
lowest_util_building  = min(avg_utilization,           key=avg_utilization.get)

# ── Auto Suggestions ──────────────────────────────────────
suggestions = [
    f"⚡ {highest_elec_building} has the highest electricity consumption — consider an energy audit.",
    f"🏫 {lowest_util_building} has the lowest classroom utilization ({avg_utilization[lowest_util_building]}%) — consider reassigning rooms.",
    "🌱 Switch to LED lighting in high-usage buildings to reduce electricity load.",
    "📅 Schedule maintenance during low-utilization periods to minimize disruption.",
]

buildings = list(electricity_per_building.keys())

analysis_result = {
    "buildings":              buildings,
    "electricity":            [electricity_per_building[b] for b in buildings],
    "water": [water_per_building[b] for b in buildings],
    "utilization":            [avg_utilization[b] for b in buildings],
    "highest_usage_building": highest_elec_building,
    "suggestions":            suggestions,
}

# ── Routes ────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials. Try admin / admin."
    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html", active="dashboard")


@app.route("/api/data")
def get_data():
    return jsonify(analysis_result)

@app.route("/api/electricity-data")
def electricity_data():

    building_usage = {k: int(v) for k, v in electricity_per_building.items()}
    trend = {str(k): int(v) for k, v in daily_electricity.items()}
    
    insights = [
    f"{highest_elec_building} has the highest electricity consumption.",
    f"{lowest_elec_building} is currently the most energy efficient building.",
    "Consider shifting heavy electrical loads to off-peak hours.",
    "Switching to LED lighting can significantly reduce energy usage."
]

    return jsonify({
        "total_electricity": total_electricity,
        "average_electricity": avg_electricity,
        "highest_usage_building": highest_elec_building,
        "most_efficient_building": lowest_elec_building,
        "building_usage": building_usage,
        "daily_trend": trend,
        "insights": insights
    })

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/electricity")
def electricity():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("electricity.html", active="electricity")

@app.route("/water")
def water():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("water.html", active="water")

@app.route("/classrooms")
def classrooms():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("classrooms.html", active="classrooms")

@app.route("/suggestions")
def suggestions_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("suggestions.html", active="suggestions")

# Water specific analytics
total_water = int(data["Water_Usage_Liters"].sum())
avg_water = float(round(data["Water_Usage_Liters"].mean(), 2))
highest_water_building = max(water_per_building, key=water_per_building.get)
lowest_water_building = min(water_per_building, key=water_per_building.get)
daily_water = data.groupby("Date")["Water_Usage_Liters"].sum().to_dict()

@app.route("/api/water-data")
def water_data():
    building_usage = {k: int(v) for k, v in water_per_building.items()}
    trend = {str(k): int(v) for k, v in daily_water.items()}
    insights = [
        f"{highest_water_building} has the highest water consumption.",
        f"{lowest_water_building} is currently the most water efficient building.",
        "Fix leaking taps and pipes to reduce water wastage.",
        "Install water meters per building for better tracking."
    ]
    return jsonify({
        "total_water": total_water,
        "average_water": avg_water,
        "highest_usage_building": highest_water_building,
        "most_efficient_building": lowest_water_building,
        "building_usage": building_usage,
        "daily_trend": trend,
        "insights": insights
    })

if __name__ == "__main__":
    app.run(debug=True)