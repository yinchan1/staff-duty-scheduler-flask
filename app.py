from flask import Flask, render_template, request, redirect, url_for, send_file
import json
import os
import csv

app = Flask(__name__)
FILE_NAME = "shifts.json"

# --- Base Functions ---

def load_shifts():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            return json.load(f)
    return []

def save_shifts(shifts):
    with open(FILE_NAME, "w") as f:
        json.dump(shifts, f, indent=4)

# ---  Routes ---

@app.route("/")
def index():
    shifts = load_shifts()
    # view_shifts 
    shifts = sorted(shifts, key=lambda s: (s["date"], s["time"]))
    
    # Filter by Employee or Date
    employee_query = request.args.get('employee')
    date_query = request.args.get('date')

    if employee_query:
        shifts = [s for s in shifts if employee_query.lower() in s["employee"].lower()]
    if date_query:
        shifts = [s for s in shifts if s["date"] == date_query]

    return render_template("index.html", shifts=shifts)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = request.form["date"]
        time = request.form["time"]
        employee = request.form["employee"]

        shifts = load_shifts()
        # Conflict check
        for s in shifts:
            if s["date"] == date and s["time"] == time:
                return "Shift conflict! <a href='/add'>Retry</a>"

        shifts.append({"date": date, "time": time, "employee": employee})
        save_shifts(shifts)
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route("/delete/<int:index>")
def delete(index):
    shifts = load_shifts()
    # delete_shift 
    if 0 <= index < len(shifts):
        shifts.pop(index)
        save_shifts(shifts)
    return redirect(url_for("index"))

@app.route("/export")
def export():
    shifts = load_shifts()
    if not shifts:
        return "No data to export"
    
    sorted_shifts = sorted(shifts, key=lambda x: x['date'])
    
    filename = "shifts_export.csv"
    with open(filename, "w", newline="") as f:
      
        writer = csv.DictWriter(f, fieldnames=["date", "time", "employee"])
        writer.writeheader()
        writer.writerows(sorted_shifts)
    
    return send_file(filename, as_attachment=True)




@app.route("/calendar")
def calendar():
    try:
        shifts = load_shifts()
        
        if not shifts:
            return render_template("calendar.html", dates=[], employees=[], schedule_map={}, stats={})

        
        all_dates = sorted(list(set(s["date"] for s in shifts)))
        all_employees = sorted(list(set(s["employee"] for s in shifts)))
        shift_lookup = {(s["employee"], s["date"]): s["time"] for s in shifts}
        
     
        stats = {}
        for s in shifts:
            emp = s["employee"]
            stats[emp] = stats.get(emp, 0) + 1

        return render_template("calendar.html", 
                               dates=all_dates, 
                               employees=all_employees, 
                               schedule_map=shift_lookup,
                               stats=stats)
    except Exception as e:
        print(f"Error: {e}")
        return f"System Error: {e}"


if __name__ == "__main__":
    app.run(debug=True)