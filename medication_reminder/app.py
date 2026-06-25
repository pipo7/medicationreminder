#!/usr/bin/env python3
"""
Medication Reminder App
A simple Python app that reminds users to take medications on time with voice alerts.
"""

import sys
from db import init_db, add_medication, get_all_medications
from scheduler import ReminderScheduler

def display_menu():
    """Display the main menu."""
    print("\n" + "="*50)
    print("MEDICATION REMINDER APP")
    print("="*50)
    print("1. Add a new medication")
    print("2. View all medications")
    print("3. Start reminders")
    print("4. Exit")
    print("="*50)

def add_medication_interactive():
    """Interactively add a new medication."""
    print("\n--- Add New Medication ---")
    
    name = input("Enter medication name (e.g., Aspirin): ").strip()
    if not name:
        print("❌ Medication name cannot be empty")
        return
    
    dosage = input("Enter dosage (e.g., 500mg): ").strip()
    if not dosage:
        print("❌ Dosage cannot be empty")
        return
    
    reminder_times = input("Enter reminder times (comma-separated, HH:MM format):\n  e.g., 08:00,14:00,20:00\n> ").strip()
    if not reminder_times:
        print("❌ Reminder times cannot be empty")
        return
    
    try:
        med_id = add_medication(name, dosage, reminder_times)
        print(f"✓ Medication '{name}' added successfully (ID: {med_id})")
    except Exception as e:
        print(f"❌ Error adding medication: {e}")

def view_medications():
    """Display all medications."""
    print("\n--- Your Medications ---")
    
    medications = get_all_medications()
    
    if not medications:
        print("No medications added yet.")
        return
    
    for med_id, name, dosage, reminder_times in medications:
        print(f"\n  ID: {med_id}")
        print(f"  Name: {name}")
        print(f"  Dosage: {dosage}")
        print(f"  Reminders: {reminder_times}")

def start_reminders():
    """Start the reminder scheduler."""
    medications = get_all_medications()
    
    if not medications:
        print("\n❌ No medications added. Please add medications first.")
        return
    
    print("\n🎯 Starting reminder scheduler...")
    print(f"Monitoring {len(medications)} medication(s)\n")
    
    scheduler = ReminderScheduler()
    scheduler.start()

def main():
    """Main application loop."""
    init_db()
    
    print("\n🏥 Welcome to Medication Reminder App!")
    
    while True:
        display_menu()
        choice = input("Choose an option (1-4): ").strip()
        
        if choice == "1":
            add_medication_interactive()
        elif choice == "2":
            view_medications()
        elif choice == "3":
            start_reminders()
        elif choice == "4":
            print("\n✓ Thank you for using Medication Reminder App. Stay healthy!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
