import json
import os
import csv


FILE_NAME = "shifts.json"

# Load shifts from JSON
def load_shifts():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    return []

# Save shifts to JSON
def save_shifts(shifts):
    with open(FILE_NAME, "w") as file:
        json.dump(shifts, file, indent=4)

# Add shift with conflict check
def add_shift(shifts):
    date = input("Enter date (YYYY-MM-DD): ")
    time = input("Enter time (e.g. 09:00-13:00): ")
    employee = input("Enter employee name: ")

    # Check exact duplicate shift
    for s in shifts:
        if s["date"] == date and s["time"] == time:
            print("Shift conflict! Same date and time already exists.")
            return

    shift = {
        "date": date,
        "time": time,
        "employee": employee
    }

    shifts.append(shift)
    save_shifts(shifts)
    print("Shift added successfully!")

# View shifts sorted by date & time
def view_shifts(shifts):
    if not shifts:
        print("No shifts scheduled.")
        return
    
    # Sort by date then time
    sorted_shifts = sorted(shifts, key=lambda s: (s["date"], s["time"]))
    
    print("\n--- Scheduled Shifts ---")
    for i, shift in enumerate(sorted_shifts):
        print(f"{i+1}. {shift['date']} | {shift['time']} | {shift['employee']}")
    print("------------------------")

# Delete shift
def delete_shift(shifts):
    view_shifts(shifts)
    try:
        choice = int(input("Enter shift number to delete: ")) - 1
        removed = shifts.pop(choice)
        save_shifts(shifts)
        print(f"Removed: {removed}")
    except:
        print("Invalid selection.")

# Filter employee 
def filter_by_employee(shifts):
    name = input("Enter employee name to filter: ")
    filtered = [s for s in shifts if s["employee"].lower() == name.lower()]
    
    if not filtered:
        print(f"No shifts found for {name}.")
        return
    
    print(f"\n--- Shifts for {name} ---")
    for i, shift in enumerate(filtered):
        print(f"{i+1}. {shift['date']} | {shift['time']}")
    print("-------------------------")

# Filter date
def search_by_date(shifts):
    date = input("Enter date (YYYY-MM-DD) to search: ")
    filtered = [s for s in shifts if s["date"] == date]
    
    if not filtered:
        print(f"No shifts found on {date}.")
        return
    
    print(f"\n--- Shifts on {date} ---")
    for i, shift in enumerate(filtered):
        print(f"{i+1}. {shift['time']} | {shift['employee']}")
    print("-------------------------")

def save_to_csv(shifts):
    if not shifts:
        print("No shifts to save.")
        return
    
    filename = input("Enter CSV filename (e.g. shifts.csv): ")
    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["date", "time", "employee"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for shift in shifts:
            writer.writerow(shift)
    
    print(f"Shifts saved to {filename}")

# Main menu
def main():
    shifts = load_shifts()

    while True:
        print("\n--- Shift Scheduler ---")
        print("1. Add shift")
        print("2. View shifts")
        print("3. Delete shift")
        print("4. Filter shifts by employee")
        print("5. Search shifts by date")
        print("6. Save shifts as CSV")
        print("7. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_shift(shifts)
        elif choice == "2":
            view_shifts(shifts)
        elif choice == "3":
            delete_shift(shifts)
        elif choice == "4":
            filter_by_employee(shifts)
        elif choice == "5":
            search_by_date(shifts)
        elif choice == "6":
            save_to_csv(shifts)
        elif choice == "7":
            print("Bye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()