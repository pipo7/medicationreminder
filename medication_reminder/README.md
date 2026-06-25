# Medication Reminder App

A Flask app to manage medicine reminders, mark doses as taken, and view activity logs.

## Features

- Browser-time reminders with status updates
- Admin page to add, update, and remove medications
- Mandatory user name for add logs
- Activity log history
- Bar chart of medicines taken by date

## Setup

1. Go to project folder:

```bash
cd medication_reminder
```

2. Create virtual environment (one time):

```bash
python3 -m venv venv
```

3. Activate virtual environment:

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python3 web_app.py
```

Open:

- Dashboard: http://localhost:5000
- Admin: http://localhost:5000/updates/admin

## Dashboard Behavior

- `medicine taken` button is enabled only when:
  - current browser time is equal to reminder time, or
  - current browser time is past reminder time
- Before reminder time, `medicine taken` stays disabled.
- Once clicked, the row becomes `medicine taken` and button is disabled.

## Admin Behavior

- Add medication requires:
  - Your Name
  - Medicine Name
  - Dosage
  - Reminder Times (`HH:MM`, comma separated)
- Save clears the add form after successful submit.

## Notes

- Use only `venv/` as your virtual environment.
- Database file: `data/medications.db`.
