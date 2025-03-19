from flask import render_template,redirect,url_for,flash,request,jsonify
from app import app,db
from app.models import Users,Booking,Computer,History,CurrentBooking,Admin,Security,Configurations
from app.forms import StudentRegisterForm,LoginForm,BookingForm,ChangePasswordForm
from flask_login import login_user, logout_user,  current_user,login_required
from datetime import timedelta,datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
from app.my_functions import round_robin_assignment,conflict_check,role_required,time_check,hash_password,check_password
########################
###  STUDENT SECTION ###
########################


@app.route("/student_login", methods=['GET', 'POST'])
def student_login_page():
    form = LoginForm()
    if form.validate_on_submit():
        # Fetch the user by roll number
        attempted_user = Users.query.filter_by(rollno=form.rollno.data).first()

        # Check if the user exists and the password is correct
        if attempted_user and check_password(attempted_user.password_hash, form.password.data):
            login_user(attempted_user)
            flash(f'Successfully logged in as {attempted_user.name}', 'success')
            return redirect(url_for('student_page'))  # Redirect after login
        else:
            flash('Login Unsuccessful. Check Roll No and password', 'danger')

    return render_template("student_login.html", form=form)


@app.route("/student_register", methods=['GET', 'POST'])
def student_register_page():
    form = StudentRegisterForm()
    if form.validate_on_submit():
        # Check for existing roll number, name, or email
        existing_rollno = Users.query.filter_by(rollno=form.rollno.data).first()
        existing_name = Users.query.filter_by(name=form.name.data).first()
        existing_email = Users.query.filter_by(email=form.email.data).first()

        if existing_rollno:
            flash("Error: Roll number already exists.", "danger")
        elif existing_name:
            flash("Error: Name already exists.", "danger")
        elif existing_email:
            flash("Error: Email already exists.", "danger")
        else:

            hashed_password = hash_password(form.password.data)
            # Proceed with registration
            new_student = Users(
                rollno=form.rollno.data,
                name=form.name.data,
                phone=form.phone.data,
                email=form.email.data,
                password_hash=hashed_password,  # Do hashing later
                batch=form.batch.data,
                year_of_passout=form.YOP.data
            )

            db.session.add(new_student)
            db.session.commit()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("student_login_page"))

    return render_template("student_register.html", form=form)


@app.route("/student")
@login_required
@role_required(['student'])
def student_page():
    student_bookings = Booking.query.filter_by(user_rollno=current_user.rollno).all()
    max_bookings = int(Configurations.query.filter_by(variables = "max_bookings").first().values)
    max_missed_bookings = int(Configurations.query.filter_by(variables = "max_missed").first().values)
    active_bookings = len(student_bookings)
    return render_template("student.html",student=current_user,bookings = student_bookings,
                           max_bookings = max_bookings,
                           max_missed_bookings = max_missed_bookings,
                           active_bookings = active_bookings)

@app.route('/cancel_s_booking', methods=['POST'])
@login_required
@role_required(['student'])
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


@app.route("/logout_student")
@login_required
@role_required(['student'])
def student_logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("student_login_page"))


@app.route('/make_booking', methods=['GET', 'POST'])
@login_required
@role_required(['student'])
def make_booking():
    max_duration = Configurations.query.filter_by(variables ="max_duration").first()
    min_duration = Configurations.query.filter_by(variables ="min_duration").first()
    duration_values = {
    "max": int(max_duration.values),
    "min": int(min_duration.values)
    }

    form = BookingForm()
    if form.validate_on_submit():
        start_time = form.start_time.data
        duration = form.duration.data
        end_time = start_time + timedelta(minutes=duration)

        if not time_check(start_time):
            flash('Bookings cannot be made for a past time.')
            return redirect(url_for('make_booking'))
        
        if conflict_check(start_time,end_time):
            flash('You already have a booking that overlaps with this time.')
            return redirect(url_for('make_booking'))


        # Assign a computer using Round Robin
        selected_computer = round_robin_assignment(start_time,duration)
        
        if selected_computer is None:
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

@app.route("/change_s_password", methods=["GET", "POST"])
@login_required
def change_s_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Check if the old password is correct
        if not check_password(current_user.password_hash, form.old_password.data):
            flash("Old password is incorrect.", "danger")
            return redirect(url_for("change_s_password"))

        # Hash the new password and update the database
        hashed_password = hash_password(form.new_password.data)
        current_user.password_hash = hashed_password  # Update password
        db.session.commit()  # Save to database

        flash("Password changed successfully!", "success")
        return redirect(url_for("student_page"))  # Redirect to student dashboard

    return render_template("change_s_password.html", form=form)