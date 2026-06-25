#!/usr/bin/env python3
"""Separate admin server for medication management."""

from flask import Flask, redirect, render_template, request, url_for
from db import (
    add_medication,
    get_all_medications_for_admin,
    init_db,
    remove_medication,
)

app = Flask(__name__)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        reminder_times = request.form.get("reminder_times", "").strip()
        day_type = request.form.get("day_type", "everyday").strip().lower()

        if not name or not dosage or not reminder_times:
            error = "Please fill medicine name, dosage, and reminder times."
        else:
            try:
                add_medication(name, dosage, reminder_times, day_type=day_type)
                return redirect(url_for("admin"))
            except ValueError as exc:
                error = str(exc)

    medications = get_all_medications_for_admin()
    return render_template("admin.html", medications=medications, error=error)


@app.route("/admin/delete/<int:medication_id>", methods=["POST"])
def admin_delete_medication(medication_id):
    remove_medication(medication_id)
    return redirect(url_for("admin"))


@app.route("/")
def redirect_to_admin():
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=7001, debug=True)
