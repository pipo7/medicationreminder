#!/usr/bin/env python3
"""Flask app for medication reminders - dashboard and admin on single port."""

from flask import Flask, jsonify, redirect, render_template, request, url_for
from db import (
    add_medication,
    get_all_medications_for_admin,
    get_today_reminders_with_status,
    init_db,
    mark_reminder_taken_by_id,
    remove_medication,
    update_medication_times,
    log_medication_action,
    get_medication_logs,
    get_medicines_taken_by_date,
)

app = Flask(__name__)


@app.route("/")
def index():
    reminders = get_today_reminders_with_status()
    return render_template("index.html", reminders=reminders)


@app.route("/take/<int:reminder_id>", methods=["POST"])
def take_medication(reminder_id):
    mark_reminder_taken_by_id(reminder_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})

    return redirect(url_for("index"))


@app.route("/api/reminders")
def reminders_api():
    reminders = get_today_reminders_with_status()
    return jsonify(reminders)


@app.route("/api/medicines-taken-by-date")
def medicines_taken_by_date_api():
    data = get_medicines_taken_by_date(limit_days=30)
    return jsonify(data)


@app.route("/updates/admin", methods=["GET", "POST"])
def admin():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        reminder_times = request.form.get("reminder_times", "").strip()
        day_type = request.form.get("day_type", "everyday").strip().lower()
        username = request.form.get("username", "").strip()

        if not username:
            error = "Your name is required to add medications (for logging purposes)."
        elif not name or not dosage or not reminder_times:
            error = "Please fill medicine name, dosage, and reminder times."
        else:
            try:
                med_id = add_medication(name, dosage, reminder_times, day_type=day_type)
                log_medication_action(med_id, "created", new_value=f"{name} - {dosage} - {reminder_times}", username=username)
                return redirect(url_for("admin"))
            except ValueError as exc:
                error = str(exc)

    medications = get_all_medications_for_admin()
    logs = get_medication_logs(20)
    return render_template("admin.html", medications=medications, logs=logs, error=error)


@app.route("/updates/admin/delete/<int:medication_id>", methods=["POST"])
def admin_delete_medication(medication_id):
    username = request.form.get("username", "").strip()
    if not username:
        username = "anonymous"
    log_medication_action(medication_id, "deleted", username=username)
    remove_medication(medication_id)
    return redirect(url_for("admin"))


@app.route("/updates/admin/update/<int:medication_id>", methods=["POST"])
def admin_update_medication(medication_id):
    reminder_times = request.form.get("reminder_times", "").strip()
    username = request.form.get("username", "").strip()
    if not username:
        username = "anonymous"

    if not reminder_times:
        return redirect(url_for("admin"))

    try:
        log_medication_action(medication_id, "updated_times", old_value="", new_value=reminder_times, username=username)
        update_medication_times(medication_id, reminder_times)
    except ValueError:
        pass

    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
