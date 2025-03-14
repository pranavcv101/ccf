from flask import render_template,redirect,url_for,flash,request,jsonify
from app import app,db
from app.models import Users,Booking,Computer,Lastbookedcomputer,History,CurrentBooking,Admin,Security,Configurations
from app.forms import StudentRegisterForm,LoginForm,BookingForm,AddUpdateComputerForm,RemoveComputerForm,SecurityForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta,datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
from app.my_functions import round_robin_assignment
######################
###  SECURITY SECTION ###
######################S

@app.route("/security_login",methods = ['GET' , 'POST'])
def security_login_page():
    form = LoginForm()
    if form.validate_on_submit(): 
        # Add authentication logic (check if rollNo and password are valid)
        attempted_user = Security.query.filter_by(username=form.rollno.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):  # You should hash passwords in real scenario
            login_user(attempted_user)
            flash(f'Successfully logged in as {attempted_user.username}', 'success')
            return redirect(url_for('security_page'))  # Redirect after login
        else:
            flash('Login Unsuccessful. Check Roll No and password', 'danger')
    return render_template("security_login.html" ,form = form)

@app.route('/security', methods=['GET', 'POST'])
def security_page():
    bookings = []  # Store fetched bookings
    error = None

    if request.method == 'POST':
        if 'fetch_bookings' in request.form:
            rollno = request.form.get('rollno')  # Get roll number from form
            print(f"Fetching bookings for roll number: {rollno}")

            # Fetch bookings for the given roll number
            bookings = Booking.query.filter_by(user_rollno=rollno).order_by(Booking.start_time.asc()).all()
            
            if not bookings:
                error = "No bookings found for this student." 

        elif 'unlock' in request.form:
            print("hi")
            # booking_id = request.form.get('booking')  # Get selected booking ID
            # print(f"Unlocking booking ID: {booking_id}")

            # if booking_id:
            #     booking = Booking.query.get(int(booking_id))
                
            #     if booking:
            #         # Move booking to current_bookings table
            #         new_current_booking = CurrentBooking(
            #             booking_id=booking.id,
            #             user_rollno=booking.user_rollno,
            #             created_at = booking.created_at,
            #             comp_id=booking.comp_id,
            #             start_time=booking.start_time,
            #             end_time=booking.end_time,
            #             duration=booking.duration
            #         )
            #         db.session.add(new_current_booking)
            #         db.session.delete(booking)
            #         db.session.commit()

            #         flash(f"Booking unlocked for Computer {booking.comp_id}.")
            #         return redirect(url_for('security_page'))
            #     else:
            #         error = "Invalid booking selected."
            # else:
            #     error = "No booking selected."

    return render_template('security.html', bookings=bookings, error=error)





# Dummy database (Replace with PostgreSQL)
passwords_db = {
    "user1": {"password": "abcd1234", "duration": 8},  # 120 seconds unlock time
}

@app.route('/validate_password', methods=['POST'])
def validate_password():
    data = request.json
    entered_password = data.get("password")

    for user, details in passwords_db.items():
        if details["password"] == entered_password:
            return jsonify({"status": "success", "duration": details["duration"]})

    return jsonify({"status": "failure", "message": "Incorrect password"}), 401