from flask import Flask, render_template, request, redirect, url_for, send_file
import json
import os
import csv
from datetime import datetime, timedelta

app = Flask(__name__)
SHIFTS_FILE = "shifts.json"
SETTINGS_FILE = "settings.json"

# --- basic ---

def load_data(file_name, default_value):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            return json.load(f)
    return default_value

def save_data(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

# --- Routes ---

@app.route("/")
def index():
    shifts = load_data(SHIFTS_FILE, [])
    # search
    emp_q = request.args.get('employee', '').lower()
    if emp_q:
        shifts = [s for s in shifts if emp_q in s["employee"].lower()]
    return render_template("index.html", shifts=sorted(shifts, key=lambda s: s["date"]))

# rules setting
@app.route("/settings", methods=["GET", "POST"])
def settings():
    # 讀取現有設定
    current_settings = load_data(SETTINGS_FILE, {"shift_types": [], "leave_types": []})

    if request.method == "POST":
        # 獲取表單傳過嚟嘅所有陣列資料
        names = request.form.getlist("shift_name[]")
        times = request.form.getlist("shift_time[]")
        quotas = request.form.getlist("shift_quota[]")
        
        # 重新建立 shift_types 列表
        new_shifts = []
        for i in range(len(names)):
            if names[i]: # 確保名唔係空嘅
                new_shifts.append({
                    "name": names[i],
                    "time": times[i],
                    "quota": int(quotas[i])
                })
        
        # 同樣處理 Leave
        l_names = request.form.getlist("leave_name[]")
        l_quotas = request.form.getlist("leave_quota[]")
        new_leaves = []
        for i in range(len(l_names)):
            if l_names[i]:
                new_leaves.append({
                    "name": l_names[i],
                    "quota": int(l_quotas[i])
                })

        current_settings = {"shift_types": new_shifts, "leave_types": new_leaves}
        save_data(SETTINGS_FILE, current_settings)
        return redirect(url_for("index"))

    return render_template("settings.html", settings=current_settings)


@app.route("/add", methods=["GET", "POST"])
def add():
    
    settings = load_data(SETTINGS_FILE, {"shift_types": [], "leave_types": []})
    
    if request.method == "POST":
        date = request.form["date"]
        shift_type = request.form["shift_type"]
        employee = request.form["employee"]
        shifts = load_data(SHIFTS_FILE, [])

        # --- rules check ---
        current_count = sum(1 for s in shifts if s["date"] == date and s["time"] == shift_type)
        all_rules = settings['shift_types'] + settings['leave_types']
        rule = next((r for r in all_rules if r['name'] == shift_type), None)
        
        if rule and current_count >= rule['quota']:
            return f"<h3>Quota Full!</h3><p>{shift_type} 限制 {rule['quota']} 人。</p><a href='/add'>返回</a>"

        shifts.append({"date": date, "time": shift_type, "employee": employee})
        save_data(SHIFTS_FILE, shifts)
        return redirect(url_for("index"))
    
    return render_template("add.html", settings=settings)


@app.route("/delete/<int:index>")
def delete(index):
    shifts = load_data(SHIFTS_FILE, [])
    if 0 <= index < len(shifts):
        shifts.pop(index); save_data(SHIFTS_FILE, shifts)
    return redirect(url_for("index"))




@app.route("/calendar")
def calendar():
    shifts = load_data(SHIFTS_FILE, [])
    # 獲取篩選參數
    view = request.args.get('view', 'all')
    selected_month = request.args.get('month', '')       # 格式: 2026-05
    start_date_str = request.args.get('start_date', '')   # 格式: 2026-05-01

    if not shifts:
        return render_template("calendar.html", dates=[], employees=[], schedule_map={}, stats={}, view=view)

    # 1. 獲取所有出現過嘅日期並排序
    all_dates = sorted(list(set(s["date"] for s in shifts)))
    filtered_dates = all_dates

    # 2. 執行篩選邏輯
    if view == 'month' and selected_month:
        # 只顯示開首符合 "YYYY-MM" 嘅日期
        filtered_dates = [d for d in all_dates if d.startswith(selected_month)]
    
    elif (view == '1week' or view == '2weeks') and start_date_str:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        days_to_show = 7 if view == '1week' else 14
        end_dt = start_dt + timedelta(days=days_to_show - 1)
        
        filtered_dates = [
            d for d in all_dates 
            if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ]

    # 3. 【核心】只計算「目前睇到」嘅 Shift 總數
    stats = {}
    visible_shifts = [s for s in shifts if s["date"] in filtered_dates]
    for s in visible_shifts:
        emp = s["employee"]
        stats[emp] = stats.get(emp, 0) + 1

    all_employees = sorted(list(set(s["employee"] for s in shifts)))
    schedule_map = {(s["employee"], s["date"]): s["time"] for s in shifts}

    return render_template("calendar.html", 
                       dates=filtered_dates, 
                       employees=all_employees, 
                       schedule_map=schedule_map, 
                       stats=stats,
                       view=view,
                       selected_month=selected_month, # Vital for naming
                       start_date=start_date_str)     # Vital for naming

@app.route("/export")
def export():
    shifts = load_data(SHIFTS_FILE, [])
    if not shifts:
        return "<h3>No data to export!</h3><p>Please add some shifts first.</p><a href='/'>Go Back</a>"
    
    # Sort shifts by date so the CSV is organized
    sorted_shifts = sorted(shifts, key=lambda x: x.get('date', ''))
    
    filename = "staff_roster_export.csv"
    
    # We define the headers clearly
    fieldnames = ["date", "time", "employee"]
    
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for s in sorted_shifts:
            # We use .get() to prevent the app from crashing if a field is missing
            writer.writerow({
                "date": s.get("date", "N/A"),
                "time": s.get("time", "N/A"),
                "employee": s.get("employee", "N/A")
            })
    
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
