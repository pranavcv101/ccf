from flask import render_template,redirect,url_for,flash,request,jsonify
from app import app,db
from app.models import Users,Booking,Computer,Lastbookedcomputer,History,CurrentBooking,Admin,Security,Configurations
from app.forms import StudentRegisterForm,LoginForm,BookingForm,AddUpdateComputerForm,RemoveComputerForm,SecurityForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta,datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
from app.my_functions import round_robin_assignment
########################
###  STUDENT SECTION ###
########################

@app.route("/student_login",methods = ['GET' , 'POST'])
def student_login_page():
    form = LoginForm()
    if form.validate_on_submit():
        # Add authentication logic (check if rollNo and password are valid)
        attempted_user = Users.query.filter_by(rollno=form.rollno.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):  # You should hash passwords in real scenario
            login_user(attempted_user)
            flash(f'Successfully logged in as {attempted_user.name}', 'success')
            return redirect(url_for('student_page'))  # Redirect after login
        else:
            flash('Login Unsuccessful. Check Roll No and password', 'danger')
    return render_template("student_login.html" ,form = form)

@app.route("/student_register",methods = ['GET' , 'POST'])
def student_register_page():
    form = StudentRegisterForm()
    if form.validate_on_submit():
        new_student = Users(rollno = form.rollno.data,
            name = form.name.data,
            phone = form.phone.data,
            email = form.email.data,
            password = form.password.data, #do hashing later
            batch = form.batch.data,
            year_of_passout = form.YOP.data
            )
        
        db.session.add(new_student)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('student_login_page'))
    return render_template("student_register.html",form = form)

@app.route("/student")
def student_page():
    student_bookings = Booking.query.filter_by(user_rollno=current_user.rollno).all()
    max_bookings = Configurations.query.filter_by(variables = "max_bookings").first()
    max_missed_bookings = Configurations.query.filter_by(variables = "missed_bookings").first()
    active_bookings = len(student_bookings)
    return render_template("student.html",student=current_user,bookings = student_bookings,
                           max_bookings = max_bookings,
                           max_missed_bookings = max_missed_bookings,
                           active_bookings = active_bookings)

@app.route('/cancel_s_booking', methods=['POST'])
def cancel_s_booking():
    booking_id = request.form.get('booking_id')
    booking = Booking.query.get(booking_id)

    if booking:
        db.session.delete(booking)
        db.session.commit()
        flash("Booking canceled successfully.", "success")
    else:
        flash("Invalid booking selected.", "danger")

    return redirect(url_for('student_page'))


@app.route("/logout")
@login_required
def student_logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("student_login_page"))




@app.route('/make_booking', methods=['GET', 'POST'])
@login_required
def make_booking():
    max_duration = Configurations.query.filter_by(variables ="max_duration").first()
    min_duration = Configurations.query.filter_by(variables ="min_duration").first()
    duration_values = {
    "max": max_duration.values,
    "min": min_duration.values
    }

    form = BookingForm()
    if form.validate_on_submit():
        start_time = form.start_time.data
        duration = form.duration.data
        end_time = start_time + timedelta(minutes=duration)
 
        # Assign a computer using Round Robin
        selected_computer = round_robin_assignment(start_time,duration)
        
        print("==>>Selected computers is ",selected_computer)
        if selected_computer is None:
            print("no computers availables")
            flash('No available computers for booking.')
            return redirect(url_for('make_booking'))

        # Create a new booking
        new_booking = Booking(
            user_rollno=current_user.rollno,
            comp_id=selected_computer.comp_id, 
            start_time = start_time,
            end_time = end_time,
            duration=duration
        )
        current_user.no_of_bookings+=1
        
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking successful!')
        # Redirect to booking history or any other page
        return redirect(url_for('student_page'))
    elif request.method == 'POST':
        # Log validation errors for POST requests
        print('Form validation failed:', form.errors)
    return render_template('make_booking.html', form=form,duration_values = duration_values)
