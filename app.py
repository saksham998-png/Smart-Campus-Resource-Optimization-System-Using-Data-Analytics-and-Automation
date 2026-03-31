from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "smartcampus2025"

# Load dataset
try:
    data = pd.read_csv("campus_data.csv")
except (pd.errors.EmptyDataError, FileNotFoundError):
    data = pd.read_excel("smart_campus_200_row_dataset.xlsx")
    data["Data_Type"] = "historical"
    data.to_csv("campus_data.csv", index=False)
    
data = data[data["Rooms_Used"] > 0]

    
# ── BASELINE METRICS (IMPORTANT) ──

# Per building avg per room electricity & water
data["per_room_electricity"] = data["Electricity_Units"] / data["Rooms_Used"]
data["per_room_water"] = data["Water_Usage_Liters"] / data["Rooms_Used"]

baseline_metrics = data.groupby("Building").agg({
    "per_room_electricity": "mean",
    "per_room_water": "mean"
}).round(2).to_dict("index")

# Total rooms per block (hardcoded for now)
TOTAL_ROOMS = {
    "A": 50,
    "B": 60,
    "C": 33,
    "D": 28
}

AVG_ELECTRICITY_PER_ROOM_PER_HOUR = 2   # units
AVG_WATER_PER_ROOM_PER_HOUR = 10        # liters

def calculate_kwh(rooms, time_slot):
    """Estimate energy for a planned slot."""
    peak_slots = ["9:10 - 10:00", "10:05 - 10:55", "11:00 - 11:50"]
    base = rooms * AVG_ELECTRICITY_PER_ROOM_PER_HOUR
    multiplier = 1.3 if time_slot in peak_slots else 1.0
    return round(base * multiplier, 2)

# ── Planned vs Live Comparison ───────────────────────────

def generate_live_insights(data):
    planned_data = data[data["Data_Type"] == "planned"]
    live_data    = data[data["Data_Type"] == "live"]

    insights = []

    for _, p in planned_data.iterrows():
        for _, l in live_data.iterrows():
            if (p["Building"] == l["Building"] and
                str(p["Date"])[:10] == str(l["Date"])[:10] and
                p.get("Time_Slot") == l.get("Time_Slot")):

                planned_rooms = p["Rooms_Used"]
                live_rooms    = l["Rooms_Used"]

                if planned_rooms > 0:
                    gap         = planned_rooms - live_rooms
                    gap_percent = (gap / planned_rooms) * 100

                    if gap_percent > 30:
                        insights.append({
                            "type":       "underutilization",
                            "building":   p["Building"],
                            "message":    f"{p['Building']} Block underutilized by {int(gap_percent)}%",
                            "suggestion": "Reduce electricity usage or shift classes",
                            "severity":   "medium"
                        })
                    elif gap_percent < -20:
                        insights.append({
                            "type":       "overutilization",
                            "building":   p["Building"],
                            "message":    f"{p['Building']} Block overutilized",
                            "suggestion": "Increase resources or redistribute load",
                            "severity":   "high"
                        })

    return insights

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


@app.route("/planned-entry", methods=["GET", "POST"])
def planned_entry():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    plan = None

    if request.method == "POST":
        bldg      = request.form["building"]
        rooms     = int(request.form["rooms"])
        date      = request.form["date"]
        time_slot = request.form["time_slot"]
        hours     = 1

        # ── Confirm & Save ──
        if request.form.get("confirmed") == "1":
            per_room_elec  = baseline_metrics[bldg]["per_room_electricity"]
            per_room_water = baseline_metrics[bldg]["per_room_water"]

            electricity = round(rooms * per_room_elec, 2)
            water       = round(rooms * per_room_water, 2)

            new_entry = {
                "Building": bldg,
                "Electricity_Units": electricity,
                "Water_Usage_Liters": water,
                "Rooms_Used": rooms,
                "Total_Rooms": TOTAL_ROOMS[bldg],
                "Date": date,
                "Time_Slot": time_slot,
                "Data_Type": "planned"
            }

            global data
            data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
            data.to_csv("campus_data.csv", index=False)
            return redirect(url_for("dashboard"))

        # ── NEW CLEAN PLANNED LOGIC ──
        total_rooms = TOTAL_ROOMS[bldg]

        # utilization %
        utilization = round((rooms / total_rooms) * 100, 2)

        # baseline values (from dataset)
        per_room_elec  = baseline_metrics[bldg]["per_room_electricity"]
        per_room_water = baseline_metrics[bldg]["per_room_water"]

        # expected usage
        expected_electricity = round(rooms * per_room_elec, 2)
        expected_water       = round(rooms * per_room_water, 2)

        plan = {
            "building": bldg,
            "slot": time_slot,
            "date": date,
            "planned_rooms": rooms,
            "total_rooms": total_rooms,
            "utilization": utilization,
            "expected_electricity": expected_electricity,
            "expected_water": expected_water
        }

    return render_template("planned_entry.html", plan=plan)

@app.route("/live-entry", methods=["GET", "POST"])
def live_entry():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    result = None

    if request.method == "POST":
        bldg      = request.form["building"]
        rooms     = int(request.form["rooms"])
        date      = request.form["date"]
        time_slot = request.form["time_slot"]
        hours     = 1
        electricity = float(request.form["electricity"])
        water       = float(request.form["water"])
        day_type    = request.form.get("day_type", "normal")

        utilization = round((rooms / TOTAL_ROOMS[bldg]) * 100, 2)
        per_room_elec  = baseline_metrics[bldg]["per_room_electricity"]
        per_room_water = baseline_metrics[bldg]["per_room_water"]
        
        new_entry = {
            "Building":           bldg,
            "Electricity_Units":  electricity,
            "Water_Usage_Liters": water,
            "Rooms_Used":         rooms,
            "Total_Rooms": TOTAL_ROOMS[bldg],
            "Date":               date,
            "Time_Slot":          time_slot,
            "Utilization_Percentage": utilization,
            "per_room_electricity": per_room_elec,
            "per_room_water": per_room_water,
            "Data_Type":          "live"
        }
        global data
        data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
        data.to_csv("campus_data.csv", index=False)

        # Find matching planned entry
        planned_rows = data[
            (data["Data_Type"] == "planned") &
            (data["Building"]  == bldg)      &
            (data["Time_Slot"] == time_slot) &
            (data["Date"].astype(str).str[:10] == str(date)[:10])
        ]
        planned_rooms = int(planned_rows.iloc[0]["Rooms_Used"]) if not planned_rows.empty else None

        # Gap analysis
        if planned_rooms is not None:
            gap     = planned_rooms - rooms
            gap_pct = round((gap / planned_rooms) * 100, 1) if planned_rooms > 0 else 0
            if gap_pct > 30:
                status       = "underutilized"
                status_msg   = f"Underutilized by {abs(gap_pct)}%"
                status_color = "#f0a500"
            elif gap_pct < -20:
                status       = "overutilized"
                status_msg   = f"Overutilized by {abs(gap_pct)}%"
                status_color = "#e05555"
            else:
                status       = "optimal"
                status_msg   = "Usage is optimal"
                status_color = "#2e9e6b"
        else:
            gap, gap_pct, status = 0, 0, "no_plan"
            status_msg   = "No planned entry found for this slot"
            status_color = "#888"


        result = {
            "building":      bldg,
            "slot":          time_slot,
            "date":          date,
            "live_rooms":    rooms,
            "planned_rooms": planned_rooms,
            "gap":           gap,
            "gap_pct":       gap_pct,
            "status":        status,
            "status_msg":    status_msg,
            "status_color":  status_color,
            "electricity":   electricity,
            "water":         water,
        }

    return render_template("live_entry.html", result=result)


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


@app.route("/analysis")
def analysis():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("analysis.html", active="analysis")


@app.route("/api/live-dashboard")
def live_dashboard():
    """
    KPI data for dashboard — computed from LIVE entries only.
    Falls back gracefully if no live data exists yet.
    """
    global data
    live = data[data["Data_Type"] == "live"].copy()

    if live.empty:
        return jsonify({
            "has_data": False,
            "buildings": [],
            "avg_electricity": {},
            "avg_water": {},
            "avg_utilization": {},
            "total_entries": 0,
            "suggestions": [
                "No live entries yet — add live data via the Live Entry form.",
                "🌱 Switch to LED lighting to reduce electricity load.",
                "📅 Schedule maintenance during low-utilization periods.",
            ]
        })

    live["Utilization_Percentage"] = (live["Rooms_Used"] / live["Total_Rooms"]) * 100

    avg_elec  = live.groupby("Building")["Electricity_Units"].mean().round(2).to_dict()
    avg_water = live.groupby("Building")["Water_Usage_Liters"].mean().round(2).to_dict()
    avg_util  = live.groupby("Building")["Utilization_Percentage"].mean().round(2).to_dict()

    buildings = sorted(set(avg_elec) | set(avg_water) | set(avg_util))

    highest_elec = max(avg_elec, key=avg_elec.get) if avg_elec else "—"
    lowest_util  = min(avg_util,  key=avg_util.get)  if avg_util  else "—"

    suggestions = [
        f"⚡ Block {highest_elec} has the highest avg electricity — consider an energy audit.",
        f"🏫 Block {lowest_util} has the lowest avg utilization ({avg_util.get(lowest_util, 0):.1f}%) — consider reassigning rooms.",
        "🌱 Switch to LED lighting in high-usage buildings to reduce electricity load.",
        "📅 Schedule maintenance during low-utilization periods to minimize disruption.",
    ]

    return jsonify({
        "has_data":        True,
        "buildings":       buildings,
        "avg_electricity": {b: avg_elec.get(b,  0) for b in buildings},
        "avg_water":       {b: avg_water.get(b, 0) for b in buildings},
        "avg_utilization": {b: avg_util.get(b,  0) for b in buildings},
        "total_entries":   len(live),
        "highest_elec_building": highest_elec,
        "suggestions":     suggestions,
    })


@app.route("/api/analysis")
def analysis_api():
    """
    Planned vs Live comparison filtered by date range.
    Query params: date_from, date_to  (YYYY-MM-DD, both optional)
    """
    global data
    date_from = request.args.get("date_from", "")
    date_to   = request.args.get("date_to",   "")

    planned = data[data["Data_Type"] == "planned"].copy()
    live    = data[data["Data_Type"] == "live"].copy()

    # normalise
    planned["_date"] = planned["Date"].astype(str).str[:10]
    live["_date"]    = live["Date"].astype(str).str[:10]
    planned["_slot"] = planned["Time_Slot"].astype(str).str.strip()
    live["_slot"]    = live["Time_Slot"].astype(str).str.strip()

    # apply date filter
    if date_from:
        planned = planned[planned["_date"] >= date_from]
        live    = live[live["_date"]    >= date_from]
    if date_to:
        planned = planned[planned["_date"] <= date_to]
        live    = live[live["_date"]    <= date_to]

    # available dates (union of planned + live in range)
    all_dates = sorted(set(planned["_date"].tolist()) | set(live["_date"].tolist()))

    matches = []
    for _, p in planned.iterrows():
        matched = live[
            (live["Building"] == p["Building"]) &
            (live["_date"]    == p["_date"])    &
            (live["_slot"]    == p["_slot"])
        ]
        for _, l in matched.iterrows():
            p_elec  = float(p["Electricity_Units"])
            l_elec  = float(l["Electricity_Units"])
            p_water = float(p["Water_Usage_Liters"])
            l_water = float(l["Water_Usage_Liters"])
            p_rooms = int(p["Rooms_Used"])
            l_rooms = int(l["Rooms_Used"])

            def diff_pct(plan, actual):
                if plan == 0: return 0
                return round(((actual - plan) / plan) * 100, 1)

            def severity(pct):
                if abs(pct) > 30: return "high"
                if abs(pct) > 10: return "medium"
                return "ok"

            ed = diff_pct(p_elec,  l_elec)
            wd = diff_pct(p_water, l_water)
            rd = diff_pct(p_rooms, l_rooms)

            matches.append({
                "building":       p["Building"],
                "date":           p["_date"],
                "slot":           p["_slot"],
                "planned_elec":   round(p_elec,  1),
                "live_elec":      round(l_elec,  1),
                "elec_diff_pct":  ed,
                "elec_severity":  severity(ed),
                "planned_water":  round(p_water, 1),
                "live_water":     round(l_water, 1),
                "water_diff_pct": wd,
                "water_severity": severity(wd),
                "planned_rooms":  p_rooms,
                "live_rooms":     l_rooms,
                "rooms_diff_pct": rd,
                "rooms_severity": severity(rd),
            })

    blocks = ["A", "B", "C", "D"]
    block_summary = {}
    for b in blocks:
        bm = [m for m in matches if m["building"] == b]
        if bm:
            block_summary[b] = {
                "count":               len(bm),
                "avg_elec_diff":       round(sum(m["elec_diff_pct"]  for m in bm) / len(bm), 1),
                "avg_water_diff":      round(sum(m["water_diff_pct"] for m in bm) / len(bm), 1),
                "avg_rooms_diff":      round(sum(m["rooms_diff_pct"] for m in bm) / len(bm), 1),
                "total_planned_elec":  round(sum(m["planned_elec"]   for m in bm), 1),
                "total_live_elec":     round(sum(m["live_elec"]      for m in bm), 1),
                "total_planned_water": round(sum(m["planned_water"]  for m in bm), 1),
                "total_live_water":    round(sum(m["live_water"]     for m in bm), 1),
                "total_planned_rooms": sum(m["planned_rooms"] for m in bm),
                "total_live_rooms":    sum(m["live_rooms"]    for m in bm),
            }
        else:
            block_summary[b] = {"count": 0}

    return jsonify({
        "matches":       matches,
        "block_summary": block_summary,
        "total_matched": len(matches),
        "available_dates": all_dates,
        "date_from": date_from,
        "date_to":   date_to,
    })


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Analysis (run after routes, uses only startup data) ──

electricity_per_building = data.groupby("Building")["Electricity_Units"].sum().to_dict()
water_per_building       = data.groupby("Building")["Water_Usage_Liters"].sum().to_dict()

total_electricity     = int(data["Electricity_Units"].sum())
avg_electricity       = float(round(data["Electricity_Units"].mean(), 2))
highest_elec_building = max(electricity_per_building, key=electricity_per_building.get)
lowest_elec_building  = min(electricity_per_building, key=electricity_per_building.get)
daily_electricity     = data.groupby("Date")["Electricity_Units"].sum().to_dict()

data["Utilization_Percentage"] = (data["Rooms_Used"] / data["Total_Rooms"]) * 100
avg_utilization      = data.groupby("Building")["Utilization_Percentage"].mean().round(2).to_dict()
lowest_util_building = min(avg_utilization, key=avg_utilization.get)

CAMPUS_UTIL_MEDIAN = 65.0
building_means     = data.groupby("Building")["Electricity_Units"].mean().to_dict()

wastage_alerts          = []
building_wastage_units  = {}
building_wastage_counts = {}
glitch_count = 0
event_count  = 0

for _, row in data.iterrows():
    b           = row["Building"]
    units       = int(row["Electricity_Units"])
    b_mean      = building_means[b]
    utilization = float((row["Rooms_Used"] / row["Total_Rooms"]) * 100)

    if units > b_mean:
        if utilization < CAMPUS_UTIL_MEDIAN:
            alert_type = "sensor_glitch"
            reason     = (
                f"Only {round(utilization)}% rooms occupied but electricity is "
                f"above {b}'s average ({round(b_mean)} units) — "
                f"possible faulty sensor or equipment left on."
            )
            action = f"Contact maintenance — inspect sensors in Block {b} immediately."
            glitch_count += 1
        else:
            alert_type = "campus_event"
            reason     = (
                f"{round(utilization)}% rooms are active and usage exceeds "
                f"Block {b}'s average ({round(b_mean)} units) — "
                f"likely a scheduled event, exam session, or authorised after-hours use."
            )
            action = "No action needed — high usage is justified by campus activity."
            event_count += 1

        wastage_alerts.append({
            "building": b,
            "units":    units,
            "date":     str(row["Date"])[:10],
            "type":     alert_type,
            "reason":   reason,
            "action":   action,
        })
        building_wastage_units[b]  = building_wastage_units.get(b, 0) + units
        building_wastage_counts[b] = building_wastage_counts.get(b, 0) + 1

wastage_alerts_top4 = sorted(wastage_alerts, key=lambda x: x["units"], reverse=True)[:4]

suggestions = [
    f"⚡ {highest_elec_building} has the highest electricity consumption — consider an energy audit.",
    f"🏫 {lowest_util_building} has the lowest classroom utilization ({avg_utilization[lowest_util_building]}%) — consider reassigning rooms.",
    "🌱 Switch to LED lighting in high-usage buildings to reduce electricity load.",
    "📅 Schedule maintenance during low-utilization periods to minimize disruption.",
]

buildings     = list(electricity_per_building.keys())
live_insights = generate_live_insights(data)

analysis_result = {
    "buildings":              buildings,
    "electricity":            [electricity_per_building[b] for b in buildings],
    "water":                  [water_per_building[b] for b in buildings],
    "utilization":            [avg_utilization[b] for b in buildings],
    "highest_usage_building": highest_elec_building,
    "suggestions":            suggestions,
    "live_insights":          live_insights,
}

total_water            = int(data["Water_Usage_Liters"].sum())
avg_water              = float(round(data["Water_Usage_Liters"].mean(), 2))
highest_water_building = max(water_per_building, key=water_per_building.get)
lowest_water_building  = min(water_per_building, key=water_per_building.get)
daily_water            = data.groupby("Date")["Water_Usage_Liters"].sum().to_dict()


@app.route("/api/data")
def get_data():
    return jsonify(analysis_result)


@app.route("/api/electricity-data")
def electricity_data():
    return jsonify({
        "buildings":              buildings,
        "electricity":            [int(electricity_per_building[b]) for b in buildings],
        "utilization":            [float(avg_utilization[b]) for b in buildings],
        "total_electricity":      total_electricity,
        "average_electricity":    avg_electricity,
        "highest_usage_building": highest_elec_building,
        "most_efficient_building": lowest_elec_building,
        "building_usage":         {k: int(v) for k, v in electricity_per_building.items()},
        "daily_trend":            {str(k): int(v) for k, v in daily_electricity.items()},
        "wastage_alerts":         wastage_alerts_top4,
        "building_wastage_units": building_wastage_units,
        "building_wastage_counts": building_wastage_counts,
        "glitch_count":           glitch_count,
        "event_count":            event_count,
        "total_wastage_events":   len(wastage_alerts),
    })


@app.route("/api/water-data")
def water_data():
    insights = [
        f"{highest_water_building} has the highest water consumption.",
        f"{lowest_water_building} is currently the most water efficient building.",
        "Fix leaking taps and pipes to reduce water wastage.",
        "Install water meters per building for better tracking."
    ]
    return jsonify({
        "total_water":             total_water,
        "average_water":           avg_water,
        "highest_usage_building":  highest_water_building,
        "most_efficient_building": lowest_water_building,
        "building_usage":          {k: int(v) for k, v in water_per_building.items()},
        "daily_trend":             {str(k): int(v) for k, v in daily_water.items()},
        "insights":                insights,
    })


@app.route('/api/comparison')
def comparison_data():
    """
    Returns planned vs live comparison per block for electricity, water, and rooms.
    Each matched pair (same building + date + time_slot) becomes one comparison entry.
    """
    global data
    planned = data[data["Data_Type"] == "planned"].copy()
    live    = data[data["Data_Type"] == "live"].copy()

    # normalise date to string YYYY-MM-DD
    planned["_date"] = planned["Date"].astype(str).str[:10]
    live["_date"]    = live["Date"].astype(str).str[:10]

    # normalise time_slot to string (some rows saved as int like 1, 4)
    planned["_slot"] = planned["Time_Slot"].astype(str).str.strip()
    live["_slot"]    = live["Time_Slot"].astype(str).str.strip()

    matches = []
    for _, p in planned.iterrows():
        matched = live[
            (live["Building"] == p["Building"]) &
            (live["_date"]    == p["_date"])    &
            (live["_slot"]    == p["_slot"])
        ]
        for _, l in matched.iterrows():
            p_elec  = float(p["Electricity_Units"])
            l_elec  = float(l["Electricity_Units"])
            p_water = float(p["Water_Usage_Liters"])
            l_water = float(l["Water_Usage_Liters"])
            p_rooms = int(p["Rooms_Used"])
            l_rooms = int(l["Rooms_Used"])

            def diff_pct(plan, actual):
                if plan == 0: return 0
                return round(((actual - plan) / plan) * 100, 1)

            def severity(pct):
                if abs(pct) > 30: return "high"
                if abs(pct) > 10: return "medium"
                return "ok"

            elec_diff  = diff_pct(p_elec,  l_elec)
            water_diff = diff_pct(p_water, l_water)
            rooms_diff = diff_pct(p_rooms, l_rooms)

            matches.append({
                "building":      p["Building"],
                "date":          p["_date"],
                "slot":          p["_slot"],
                # electricity
                "planned_elec":  round(p_elec, 1),
                "live_elec":     round(l_elec, 1),
                "elec_diff_pct": elec_diff,
                "elec_severity": severity(elec_diff),
                # water
                "planned_water": round(p_water, 1),
                "live_water":    round(l_water, 1),
                "water_diff_pct": water_diff,
                "water_severity": severity(water_diff),
                # rooms
                "planned_rooms": p_rooms,
                "live_rooms":    l_rooms,
                "rooms_diff_pct": rooms_diff,
                "rooms_severity": severity(rooms_diff),
            })

    # ── per-block aggregates for the summary cards ──
    blocks = ["A", "B", "C", "D"]
    block_summary = {}
    for b in blocks:
        bm = [m for m in matches if m["building"] == b]
        if bm:
            block_summary[b] = {
                "count": len(bm),
                "avg_elec_diff":  round(sum(m["elec_diff_pct"]  for m in bm) / len(bm), 1),
                "avg_water_diff": round(sum(m["water_diff_pct"] for m in bm) / len(bm), 1),
                "avg_rooms_diff": round(sum(m["rooms_diff_pct"] for m in bm) / len(bm), 1),
                "total_planned_elec":  round(sum(m["planned_elec"]  for m in bm), 1),
                "total_live_elec":     round(sum(m["live_elec"]     for m in bm), 1),
                "total_planned_water": round(sum(m["planned_water"] for m in bm), 1),
                "total_live_water":    round(sum(m["live_water"]    for m in bm), 1),
                "total_planned_rooms": sum(m["planned_rooms"] for m in bm),
                "total_live_rooms":    sum(m["live_rooms"]    for m in bm),
            }
        else:
            block_summary[b] = {"count": 0}

    return jsonify({
        "matches":       matches,
        "block_summary": block_summary,
        "total_matched": len(matches),
    })


@app.route('/calendar')
def calendar():
    return render_template('calendar.html', active='calendar')
  
if __name__ == "__main__":
    app.run(debug=True)