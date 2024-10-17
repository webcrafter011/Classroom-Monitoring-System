import os
from cs50 import SQL
from datetime import date, datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from helper import apology
from functools import wraps
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Configure email settings
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "manujchaudhari456@gmail.com"  # Replace with your email
app.config["MAIL_PASSWORD"] = "fgjb vwgt ibfy iryv"  # Use your App Password
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)

# Initialize APScheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database connection
db = SQL("sqlite:///classroom.db")

# Create the timetable table if it doesn't exist
db.execute(
    """
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        lecture_time TEXT NOT NULL,
        teacher_name TEXT NOT NULL,
        teacher_email TEXT NOT NULL,
        lecture_date DATE NOT NULL,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Function to send email
def send_email(
    teacher_email, teacher_name, subject_name, lecture_time, lecture_id, lecture_date
):
    with app.app_context():
        confirm_url = url_for(
            "confirm_lecture",
            lecture_id=lecture_id,
            lecture_date=lecture_date,
            _external=True,
        )
        cancel_url = url_for(
            "cancel_lecture",
            lecture_id=lecture_id,
            lecture_date=lecture_date,
            _external=True,
        )

        msg = Message(
            "Lecture Status Confirmation",
            sender=app.config["MAIL_USERNAME"],
            recipients=[teacher_email],
        )
        msg.body = f"""
        Hello {teacher_name},

        This is a reminder that you have a lecture for the subject '{subject_name}' scheduled at {lecture_time} on {lecture_date}.
        
        Please confirm whether the lecture will take place or if it will be canceled by clicking the links below:

        Confirm Lecture: {confirm_url}
        Cancel Lecture: {cancel_url}

        Thank you!
        """
        mail.send(msg)
        print(f"Email sent to {teacher_email} at {datetime.now()}")


# Function to send emails to all teachers at their respective times
def send_emails_for_day(selected_date):
    lectures = db.execute(
        "SELECT id, teacher_email, teacher_name, subject_name, lecture_time FROM timetable WHERE lecture_date = ?",
        selected_date,
    )

    for lecture in lectures:
        teacher_email = lecture["teacher_email"]
        teacher_name = lecture["teacher_name"]
        subject_name = lecture["subject_name"]
        lecture_time = lecture["lecture_time"]
        lecture_id = lecture["id"]  # Get the lecture ID

        # Convert lecture_time to datetime
        now = datetime.now()
        lecture_datetime = datetime.strptime(lecture_time, "%H:%M").replace(
            year=now.year, month=now.month, day=int(selected_date.split("-")[2])
        )

        # If the lecture time is in the past for today, schedule it for tomorrow
        if lecture_datetime < now:
            lecture_datetime += timedelta(days=1)

        # Schedule email sending at lecture time
        scheduler.add_job(
            func=send_email,
            trigger="date",
            run_date=lecture_datetime,
            args=[
                teacher_email,
                teacher_name,
                subject_name,
                lecture_time,
                lecture_id,
                selected_date,
            ],
        )


@app.route("/")
def home():
    return render_template("layout.html", css_file="css/layoutStyles.css")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            session["user_id"] = 1  # Set a fixed user ID for admin
            return redirect("/")
        else:
            return apology("invalid username and/or password", 403)

    else:
        return render_template("login.html", css_file="css/layoutStyles.css")


@app.route("/timetable")
@login_required
def timetable():
    current_date = date.today().strftime("%Y-%m-%d")
    existing_lectures = db.execute(
        "SELECT COUNT(*) as count FROM timetable WHERE lecture_date = ?", current_date
    )[0]["count"]

    return render_template(
        "timetable.html",
        css_file="css/timetableStyles.css",
        current_date=current_date,
        show_display_button=(existing_lectures >= 4),
    )


@app.route("/save_timetable", methods=["POST"])
@login_required
def save_timetable():
    subject_name = request.form.get("subject_name")
    lecture_time = request.form.get("lecture_time")
    teacher_name = request.form.get("teacher_name")
    teacher_email = request.form.get("teacher_email")
    lecture_date = request.form.get("lecture_date") or date.today().strftime("%Y-%m-%d")

    # Check how many lectures are scheduled for the selected date
    existing_lectures = db.execute(
        "SELECT COUNT(*) as count FROM timetable WHERE lecture_date = ?", lecture_date
    )[0]["count"]

    if existing_lectures >= 4:
        flash("Cannot schedule more than 4 lectures for this day.", "error")
        return redirect("/timetable")

    # Insert new timetable entry
    db.execute(
        "INSERT INTO timetable (subject_name, lecture_time, teacher_name, teacher_email, lecture_date) VALUES (?, ?, ?, ?, ?)",
        subject_name,
        lecture_time,
        teacher_name,
        teacher_email,
        lecture_date,
    )

    # Schedule emails for all teachers for the selected date
    send_emails_for_day(lecture_date)

    flash("Timetable saved successfully!")
    return redirect("/timetable")


@app.route("/display_timetable", methods=["GET"])
@login_required
def display_timetable():
    selected_date = request.args.get("date")
    lectures = db.execute(
        "SELECT subject_name, lecture_time, teacher_name, teacher_email, status FROM timetable WHERE lecture_date = ?",
        selected_date,
    )
    return render_template(
        "display_timetable.html",
        lectures=lectures,
        selected_date=selected_date,
        css_file="css/timetableStyles.css",
    )


@app.route("/clear_timetable/<string:selected_date>", methods=["POST"])
@login_required
def clear_timetable(selected_date):
    # Remove all lectures for the selected date from the timetable
    db.execute("DELETE FROM timetable WHERE lecture_date = ?", (selected_date,))

    flash("Timetable cleared successfully!")
    return redirect(url_for("display_timetable", date=selected_date))


@app.route("/confirm_lecture/<int:lecture_id>/<string:lecture_date>")
def confirm_lecture(lecture_id, lecture_date):
    # Update the status of the lecture to 'Confirmed'
    db.execute(
        "UPDATE timetable SET status = ? WHERE id = ?", ("Confirmed", lecture_id)
    )

    flash("Lecture confirmed successfully!")
    return redirect(url_for("display_timetable", date=lecture_date))


@app.route("/cancel_lecture/<int:lecture_id>/<string:lecture_date>")
def cancel_lecture(lecture_id, lecture_date):
    # Update the status of the lecture to 'Canceled'
    db.execute("UPDATE timetable SET status = ? WHERE id = ?", ("Canceled", lecture_id))

    flash("Lecture canceled successfully!")
    return redirect(url_for("display_timetable", date=lecture_date))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
