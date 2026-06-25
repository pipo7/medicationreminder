import schedule
import time
from datetime import datetime
from db import get_all_medications, is_today_reminder_taken, sync_today_reminders

class ReminderScheduler:
    """Manage scheduled medication reminders."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduled_jobs = {}
        self.running = False
    
    def add_reminders_for_medications(self):
        """Schedule reminders for all active medications."""
        medications = get_all_medications()
        
        for med_id, med_name, dosage, reminder_times in medications:
            # Parse reminder times (e.g., "08:00,14:00,20:00")
            times = reminder_times.split(',')
            
            for time_str in times:
                time_str = time_str.strip()
                job_key = f"{med_id}_{time_str}"
                
                # Remove existing job if it exists
                if job_key in self.scheduled_jobs:
                    schedule.cancel_job(self.scheduled_jobs[job_key])
                
                # Schedule the reminder
                job = schedule.at(time_str).do(
                    self.remind_and_log,
                    med_id=med_id,
                    med_name=med_name,
                    dosage=dosage,
                    reminder_time=time_str
                )
                
                self.scheduled_jobs[job_key] = job
                print(f"✓ Scheduled reminder for {med_name} at {time_str}")
    
    def remind_and_log(self, med_id, med_name, dosage, reminder_time):
        """Trigger a reminder and log it.
        
        Args:
            med_id: Medication ID
            med_name: Medication name
            dosage: Dosage information
            reminder_time: Time of the reminder
        """
        sync_today_reminders()
        if is_today_reminder_taken(med_id, reminder_time):
            print(f"Skipping alarm for {med_name} at {reminder_time} (already taken)")
            return

        print(f"\n{'='*50}")
        print(f"⏰ REMINDER: Take {med_name} ({dosage})")
        print(f"{'='*50}\n")
        
        # Log the reminder (automatically mark as pending)
        print(f"Reminder logged at {datetime.now().strftime('%H:%M:%S')}")
    
    def start(self):
        """Start the reminder scheduler."""
        self.running = True
        sync_today_reminders()
        self.add_reminders_for_medications()
        
        print("\n🚀 Medication Reminder App Started")
        print("Type 'quit' to exit, 'status' for medication list\n")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)  # Check every second
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        print("\n✓ Scheduler stopped. Stay healthy!")
