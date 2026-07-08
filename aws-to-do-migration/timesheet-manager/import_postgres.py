import os
import sqlite3

import psycopg2
import psycopg2.extras

from app import DATABASE, app, init_db


SOURCE_DATABASE_URL = os.environ["SOURCE_DATABASE_URL"]


def main():
    with app.app_context():
        init_db()
    target = sqlite3.connect(DATABASE)
    target.execute("PRAGMA foreign_keys = OFF")
    target.executescript(
        """
        DELETE FROM timesheet_entries;
        DELETE FROM project_developers;
        DELETE FROM projects;
        DELETE FROM users;
        """
    )

    source = psycopg2.connect(SOURCE_DATABASE_URL)
    with source.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("SELECT id, username, is_admin, has_email_reminders FROM users ORDER BY id")
        users = cursor.fetchall()
        cursor.execute("SELECT id, name, client, currency, maximum_hours, end_date, is_maintenance FROM projects ORDER BY id")
        projects = cursor.fetchall()
        cursor.execute("SELECT id, hourly_rate, developer_id, project_id, max_hours, active FROM project_developers ORDER BY id")
        project_developers = cursor.fetchall()
        cursor.execute("SELECT id, date, hours, hourly_rate, description, developer_id, project_id, paid_work FROM timesheet ORDER BY id")
        entries = cursor.fetchall()

    for user in users:
        target.execute(
            "INSERT INTO users (id, email, name, is_admin, has_email_reminders) VALUES (?, ?, ?, ?, ?)",
            (user["id"], user["username"].lower(), user["username"].lower(), 1 if user["is_admin"] else 0, 1 if user["has_email_reminders"] else 0),
        )

    for project in projects:
        target.execute(
            """
            INSERT INTO projects (id, name, client, currency, maximum_hours, end_date, is_maintenance, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                project["id"],
                project["name"],
                project["client"],
                project["currency"],
                project["maximum_hours"],
                project["end_date"].date().isoformat() if project["end_date"] else None,
                1 if project["is_maintenance"] else 0,
            ),
        )

    for link in project_developers:
        target.execute(
            """
            INSERT INTO project_developers (id, hourly_rate, developer_id, project_id, max_hours, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (link["id"], link["hourly_rate"], link["developer_id"], link["project_id"], link["max_hours"], 1 if link["active"] else 0),
        )

    for entry in entries:
        target.execute(
            """
            INSERT INTO timesheet_entries (id, entry_date, user_id, project_id, hours, hourly_rate, paid_work, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry["id"],
                entry["date"].date().isoformat(),
                entry["developer_id"],
                entry["project_id"],
                entry["hours"],
                entry["hourly_rate"],
                1 if entry["paid_work"] else 0,
                entry["description"],
            ),
        )

    target.commit()
    target.execute("PRAGMA foreign_keys = ON")
    counts = {
        name: target.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in ["users", "projects", "project_developers", "timesheet_entries"]
    }
    target.close()
    source.close()
    print(counts)


if __name__ == "__main__":
    main()
