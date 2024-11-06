# Classroom Monitoring System

The **Classroom Monitoring System** is a web application that displays the daily lecture schedule for a classroom and facilitates real-time updates on the status of each lecture. This project provides a platform where teachers can confirm or cancel their scheduled lectures, and the information is updated on a P10 display module in the classroom. 

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Technology Stack](#technology-stack)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)

## Features

- **Admin Panel for Timetable Editing**: Admins can edit the timetable, including subject names, timings, teacher information, and email.
- **Lecture Status Updates**: Teachers receive emails with links to confirm or cancel their lectures, updating the status in real-time.
- **Clear Timetable Functionality**: Admins can clear the timetable with a single button click, with no redirection to another page.
- **Classroom Display Integration**: Lecture status (confirmed or canceled) is shown on a P10 display in the classroom.
- **Bootstrap-Based UI**: The frontend utilizes Bootstrap for responsive and clean design.
- **ESP32 and WiFi Module Support**: The system fetches updates via WiFi for display on the P10 module.

## Project Structure

```plaintext
ClassroomMonitoringSystem/
├── templates/
│   ├── apology.html               # apology for incorrect data entry
│   ├── display_timetable.html     # template to show timetable 
│   ├── layout.html                # layout of the base html page
│   ├── login.html                 # login page to login as admin
│   ├── status_confirmed.html      # Page displayed after a lecture is confirmed
│   ├── status_canceled.html       # Page displayed after a lecture is canceled
│   ├── timetable.html             # page to edit timetable
├── static/
│   ├── css/                       # Contains Bootstrap CSS
│   ├── images/                    # Contains all the static images
├── app.py                         # Flask application and route definitions
├── helper.py                      # This file contains all the helper functions used in app.py
├── classroom.db                   # Database for the webapp
└── esp32.cpp                      # this code piece would connect display to webapp through api
```
## Installation
1. Clone the repository:
```
git clone https://github.com/webcrafter011/Classroom-Monitoring-System.git
cd ClassroomMonitoringSystem
```
2. Install dependencies
```
pip install -r requirements.txt
```
3. Start ngrok
[How to setup ngrok on windows](https://www.youtube.com/watch?v=RhZnBX0I4jI&pp=ygUdaG93IHRvIHNldHVwIG5ncm9rIG9uIHdpbmRvd3M%3D)
```
ngrok http 5000
```
4. Run flask server
   1. change the ngrok link with the link in app.py line 26
   2. change the email and app password accordingly in app.py line 19, 20
   3. ```
      flask run debug
      ```
5. Access the application

## Usage
Admin Panel:

Navigate to the /timetable route to edit the timetable. Input subject names, lecture timings, and teacher details.

Lecture Confirmation/Cancellation:
Teachers receive an email with a link to confirm or cancel their lecture.
Upon confirmation/cancellation, the status is updated in the system and displayed on the classroom's P10 display.

## Clear Timetable:
Use the "Clear Timetable" button in the admin panel to reset the timetable.

Technology Stack
Backend: Python, Flask
Frontend: HTML, Bootstrap CSS, JavaScript
Database: SQLite (or your preferred database)
Hardware: ESP32, P10 Display Module

## Future Improvements
Student Notification System: Notify students of lecture status updates in real-time.
Mobile Application: Develop a mobile app for easier teacher interaction.

## Contributors
webcrafter011 - Project lead and developer.
   
