import os
from cs50 import SQL
from datetime import date, datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helper import apology
from functools import wraps
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from flask_ngrok import run_with_ngrok  # Import Ngrok

app = Flask(__name__)
run_with_ngrok(app)  # Enable ngrok for Flask app

# Configure email settings
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "youremail@mail.com"  # Replace with your email
app.config["MAIL_PASSWORD"] = "pass pass pass pass"  # Use your App Password
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

# Configure the current URL of your app to send emails and trigger responses
app.config["BASE_URL"] = (
    "https://8db6-117-217-104-211.ngrok-free.app"  # Replace with your actual base URL
)

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

# Create the timetable table if it doesn't exist, including lecture_status
db.execute(
    """
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        lecture_time TEXT NOT NULL,
        teacher_name TEXT NOT NULL,
        teacher_email TEXT NOT NULL,
        lecture_date DATE NOT NULL,
        lecture_status TEXT DEFAULT 'Pending',
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


# Function to send email with confirm and cancel links
def send_email(teacher_email, teacher_name, subject_name, lecture_time, lecture_id):
    with app.app_context():  # Ensures this is within the app context
        # Use the base URL instead of request.url_root
        confirm_link = f"{app.config['BASE_URL']}/confirm_lecture/{lecture_id}"
        cancel_link = f"{app.config['BASE_URL']}/cancel_lecture/{lecture_id}"

        msg = Message(
            "Lecture Status Confirmation",
            sender=app.config["MAIL_USERNAME"],
            recipients=[teacher_email],
        )
        msg.body = f"""
        Hello {teacher_name},

        You have a lecture for the subject '{subject_name}' scheduled at {lecture_time}.
        
        Could you please confirm if the lecture will take place or cancel it using the following links?

        Confirm the lecture: {confirm_link}
        Cancel the lecture: {cancel_link}

        Kindly respond at your earliest convenience.

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
        lecture_id = lecture["id"]
        teacher_email = lecture["teacher_email"]
        teacher_name = lecture["teacher_name"]
        subject_name = lecture["subject_name"]
        lecture_time = lecture["lecture_time"]

        # Convert lecture_time to datetime
        now = datetime.now()
        lecture_datetime = datetime.strptime(lecture_time, "%H:%M").replace(
            year=now.year, month=now.month, day=int(selected_date.split("-")[2])
        )

        # If the lecture time is in the past for today, schedule it for tomorrow
        if lecture_datetime < now:
            lecture_datetime += timedelta(days=1)

        # Schedule email sending at lecture time using a normal function instead of a lambda
        scheduler.add_job(
            func=send_email,  # Directly use send_email function
            args=(
                teacher_email,
                teacher_name,
                subject_name,
                lecture_time,
                lecture_id,
            ),  # Pass arguments
            trigger="date",
            run_date=lecture_datetime,
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
        "SELECT id, subject_name, lecture_time, teacher_name, teacher_email, lecture_status FROM timetable WHERE lecture_date = ?",
        selected_date,
    )
    return render_template(
        "display_timetable.html",
        lectures=lectures,
        selected_date=selected_date,
        css_file="css/timetableStyles.css",
    )


@app.route("/clear_timetable", methods=["POST"])
@login_required
def clear_timetable():
    db.execute("DELETE FROM timetable")
    flash("Timetable cleared successfully!")
    return redirect("/timetable")


@app.route("/confirm_lecture/<int:lecture_id>")
def confirm_lecture(lecture_id):
    # Update the lecture status to 'Confirmed'
    db.execute(
        "UPDATE timetable SET lecture_status = 'Confirmed' WHERE id = ?", lecture_id
    )
    flash("Lecture confirmed successfully!")
    return render_template("status_confirmed.html", css_file="css/layoutStyles.css")


@app.route("/cancel_lecture/<int:lecture_id>")
def cancel_lecture(lecture_id):
    # Update the lecture status to 'Canceled'
    db.execute(
        "UPDATE timetable SET lecture_status = 'Canceled' WHERE id = ?", lecture_id
    )
    flash("Lecture canceled successfully!")
    return render_template("status_canceled.html", css_file="css/layoutStyles.css")


@app.route("/get_latest_lecture_status")
def get_latest_lecture_status():
    # Get today's date
    current_date = date.today().strftime("%Y-%m-%d")

    # Fetch the latest lecture status for today
    latest_lecture = db.execute(
        "SELECT subject_name, lecture_time, teacher_name, lecture_status "
        "FROM timetable WHERE lecture_date = ? ORDER BY lecture_time DESC LIMIT 1", 
        current_date
    )

    # If there's a lecture, return its status; otherwise, return a default message
    if latest_lecture:
        latest_lecture = latest_lecture[0]  # Get the first result
        return jsonify({
            'status': latest_lecture['lecture_status'],
            'subject': latest_lecture['subject_name'],
            'time': latest_lecture['lecture_time']
        })
    else:
        return jsonify({
            'status': 'No lectures scheduled',
            'subject': '',
            'time': ''
        })


@app.route("/api/timetable_status")
def api_timetable_status():
    current_date = date.today().strftime("%Y-%m-%d")
    status = db.execute(
        "SELECT subject_name, lecture_status FROM timetable WHERE lecture_date = ?",
        current_date,
    )
    return jsonify(status)


if __name__ == "__main__":
    app.config['DEBUG'] = True  # Enable debug mode
    app.run()

