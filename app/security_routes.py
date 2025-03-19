from flask import render_template,redirect,url_for,flash,request,jsonify
from app import app,db
from app.models import Users,Booking,Computer,History,CurrentBooking,Admin,Security,Configurations
from app.forms import StudentRegisterForm,LoginForm,BookingForm,AddUpdateComputerForm,RemoveComputerForm,SecurityForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta,datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
from app.my_functions import hash_password,check_password,role_required
import random
#########################
###  SECURITY SECTION ###
#########################


@app.route("/security_login", methods=['GET', 'POST'])
def security_login_page():
    form = LoginForm()
    
    if form.validate_on_submit():
        # Fetch the security user by username
        attempted_user = Security.query.filter_by(username=form.rollno.data).first()

        # Check if the user exists and the password is correct
        if attempted_user and check_password(attempted_user.password_hash, form.password.data):
            login_user(attempted_user)
            flash(f'Successfully logged in as {attempted_user.username}', 'success')
            return redirect(url_for('security_page'))  # Redirect after login
        else:
            flash('Login Unsuccessful. Check Username and Password', 'danger')

    return render_template("security_login.html", form=form)


@app.route("/logout_security")
# @login_required
# @role_required(['security'])
def security_logout_page():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("security_login_page"))  # Redirect to security login page

@app.route('/security', methods=['GET', 'POST'])
# @login_required
# @role_required(['security'])
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
            booking_id = request.form.get('booking')  # Get selected booking ID
            print(f"Unlocking booking ID: {booking_id}")

            if booking_id:
                booking = Booking.query.get(int(booking_id))
                
                if booking:
                    # Fetch computer details
                    computer = Computer.query.get(booking.comp_id)
                    if not computer:
                        error = "Computer not found."
                    else:
                        try:
                            # Generate a random OTP (4-digit)
                            otp = random.randint(1000, 9999)

                            # Move booking to current_bookings table
                            new_current_booking = CurrentBooking(
                                booking_id=booking.id,
                                user_rollno=booking.user_rollno,
                                comp_id=booking.comp_id,
                                created_at=booking.created_at,
                                start_time=booking.start_time,
                                end_time=booking.end_time,
                                duration=booking.duration,
                                otp=otp,
                                ip_address=computer.ip_address  # Fetch from Computer model
                            )
                            db.session.add(new_current_booking)
                            db.session.delete(booking)
                            db.session.commit()

                            flash(f"Booking unlocked for Computer {booking.comp_id}. OTP: {otp}", "success")
                            return redirect(url_for('security_page'))
                        except Exception as e:
                            db.session.rollback()
                            error = f"An error occurred: {str(e)}"
                else:
                    error = "Invalid booking selected."
            else:
                error = "No booking selected."

    return render_template('security.html', bookings=bookings, error=error)





# # Dummy database (Replace with PostgreSQL)
# passwords_db = {
#     "user1": {"password": "abcd1234", "duration": 8},  # 120 seconds unlock time
# }

# @app.route('/validate_password', methods=['POST'])
# def validate_password():
#     data = request.json
#     entered_password = data.get("password")

#     for user, details in passwords_db.items():
#         if details["password"] == entered_password:
#             return jsonify({"status": "success", "duration": details["duration"]})

#     return jsonify({"status": "failure", "message": "Incorrect password"}), 401




# Endpoint 1: Validate Password
@app.route('/validate_password', methods=['POST'])
def validate_password():
    data = request.json
    comp_id = data.get('comp_id')
    otp = data.get('otp')

    if not comp_id or not otp:
        return jsonify({'message': 'Missing comp_id or otp'}), 400

    # Check if a booking exists for the given computer ID
    booking = CurrentBooking.query.filter_by(comp_id=comp_id).first()

    if not booking:
        return jsonify({'message': 'No booking found for this computer'}), 404  # Not Found

    # Check if the OTP matches the booking
    if booking.otp != int(otp):
        return jsonify({'message': 'Incorrect OTP'}), 401  # Unauthorized

    # If both conditions are met, return the success response
    return jsonify({
        #'duration': booking.duration * 60,  # Convert minutes to seconds
        'duration': 10,  # Convert minutes to seconds
        'booking_id': booking.booking_id
    }), 200


# Endpoint 2: Delete Booking
@app.route('/delete_booking', methods=['POST'])
def delete_booking():
    data = request.json
    booking_id = data.get('booking_id')

    if not booking_id:
        return jsonify({'message': 'Missing booking_id'}), 400

    # Find and delete booking
    booking = CurrentBooking.query.get(booking_id)
    if booking:
      # Move booking to history table
        history_entry = History(
            id=booking.booking_id,
            user_rollno=booking.user_rollno,
            comp_id=booking.comp_id,
            created_at=booking.created_at,
            start_time=booking.start_time,
            end_time=booking.end_time,
            duration=booking.duration,
            status="completed"  # Mark status as completed
        )
        db.session.add(history_entry)

        # Delete the booking from current_bookings
        db.session.delete(booking)
        db.session.commit()

        return jsonify({'message': 'Booking moved to history successfully'}), 200
    else:
        return jsonify({'message': 'Booking not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
