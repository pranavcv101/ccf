from flask import render_template,redirect,url_for,flash,request,jsonify
from app import app,db
from app.models import Users,Booking,Computer,Lastbookedcomputer,History,CurrentBooking
from app.forms import StudentRegisterForm,LoginForm,BookingForm,AddUpdateComputerForm,RemoveComputerForm,SecurityForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta,datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time

########################
###    AUTOMATION    ###
########################



def move_expired_bookings():
    with app.app_context():
        now = datetime.now()
        print("move_expired_bookings running")
        # Find expired bookings
        expired_bookings = Booking.query.filter(
            (Booking.scheduled_datetime) <= now ).all()

        if not expired_bookings:
            print("\n======history mover ::::: No expired bookings to move.")
            return

        for booking in expired_bookings:
            # Create a corresponding history record
            history_entry = History(
                user_rollno=booking.user_rollno,
                comp_id=booking.comp_id,
                created_at=booking.created_at,
                scheduled_datetime=booking.scheduled_datetime,
                duration=booking.duration,
                status='completed' if booking.status == 'active' else booking.status
            )
            db.session.add(history_entry)

            # Delete the expired booking
            db.session.delete(booking)

        db.session.commit()
        print(f"\n\n\n======history mover ::::::: Moved {len(expired_bookings)} booking(s) to history.")


start_time = time.time()
def tester():
    elapsed_time = int(time.time() - start_time)  # Calculate elapsed time in seconds
    print(f"hello tester bott, elapsed time: {elapsed_time} seconds")

# # Initialize scheduler
# scheduler1 = BackgroundScheduler()

# scheduler1.add_job(func=tester, trigger="interval", seconds=2)  # Runs every hour
# scheduler1.start() 


# subz= BackgroundScheduler()
# subz.add_job(func=tester,trigger="interval",seconds = 5)
# subz.start()

# @app.teardown_appcontext
# def shutdown_scheduler(exception=None):
#     print(f"++++\nTeardown triggered. Exception: {exception}")
#     if subz.running:
#         print("Shutting down scheduler")
#         subz.shutdown(wait=False)
#         print("Scheduler shut down.")



##################################
##################################
##################################


@app.route("/")
@app.route("/home")
def home_page():
    return render_template("home.html")


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
    return render_template("student.html",student=current_user,bookings = student_bookings)

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
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
    return render_template('make_booking.html', form=form)

def round_robin_assignment(start_time,duration_m):
    # Retrieve last booked computer
    last_booked = Lastbookedcomputer.query.first()  # Get the last booked computer

    # Get the comp_id of the last booked computer
    last_booked_comp_id = last_booked.comp_id if last_booked else None

    # Get all available computers
    computers = Computer.query.filter_by(is_available=True).all()
    print("==>> All available computers are", computers)

    # If no computers are available, return None
    if not computers:
        return None

    # Start from the last booked computer and check availability in circular manner
    start_index = next((index for index, comp in enumerate(computers) if comp.comp_id == last_booked_comp_id), -1) + 1
    
    # If the last booked computer was not found, start from the first available computer
    if start_index == -1:
        start_index = 0
    
    # Try to find an available computer by looping in a circular manner
    for i in range(len(computers)):
        current_index = (start_index + i) % len(computers)  # Circularly move through computers
        selected_computer = computers[current_index]
        
        # Check if this computer is available
        if check_availability(selected_computer, start_time, duration_m):
            # Update the last booked computer in the database
            last_booked.comp_id = selected_computer.comp_id
            db.session.commit()
            return selected_computer

    # If no computer is available after a full cycle, return None
    return None

def check_availability(selected_computer, start_time, duration_m):
    
    # end_time = scheduled_datetime + timedelta(minutes=duration)
    # Create an instance of the selected booking row
    bookings = Booking.query.filter_by(comp_id=selected_computer.comp_id).all()

    for booking in bookings:
        # Calculate the end time for the current booking
        booking_end_time = booking.start_time + timedelta(minutes=booking.duration)

        # Check for conflicts
        if (booking.start_time <= start_time < booking_end_time) or \
           (booking.start_time < start_time + timedelta(minutes=duration_m) <= booking_end_time):
            return False  # Conflict found, computer is not available
    
    return True  # The computer is available




######################
###  ADMIN SECTION ###
######################



@app.route("/admin_home")
def admin_home_page():
    return render_template("admin_home.html")

@app.route("/students_details" , methods = ['GET' , 'POST'])
def student_details_page():
    print("test")
    students = Users.query.all()
    for s in students:
        print(s.name)
    return render_template("students_details.html",students = students)




@app.route("/admin_home/booking_details")
def booking_details_page():
    # Fetch all booking records from the database
    bookings = Booking.query.all()
    return render_template("booking_details.html", bookings=bookings)






@app.route('/admin_home/computers', methods=['GET', 'POST'])
def computer_management():
    add_update_form = AddUpdateComputerForm()
    remove_form = RemoveComputerForm()

    # Handle the add/update computer form submission
    if add_update_form.validate_on_submit():
        comp_id = add_update_form.comp_id.data
        status = add_update_form.status.data
        is_available = add_update_form.is_available.data == 'True'

        existing_computer = Computer.query.filter_by(comp_id=comp_id).first()

        if existing_computer:
            # Update the existing computer
            existing_computer.status = status
            existing_computer.is_available = is_available
            db.session.commit()
            flash(f"Computer with ID {comp_id} has been updated successfully.", 'success')
        else:
            # Add a new computer
            new_computer = Computer(comp_id=comp_id, status=status, is_available=is_available)
            db.session.add(new_computer)
            db.session.commit()
            flash(f"Computer with ID {comp_id} has been added successfully.", 'success')

        return redirect(url_for('computer_management'))

    # Handle the remove computer form submission
    if remove_form.validate_on_submit():
        comp_id = remove_form.comp_id.data
        
        computer_to_remove = Computer.query.filter_by(comp_id=comp_id).first()
        
        if computer_to_remove:
            db.session.delete(computer_to_remove)
            db.session.commit()
            flash(f"Computer with ID {comp_id} has been removed successfully.", 'success')
        else:
            flash(f"No computer found with ID {comp_id}.", 'danger')

        return redirect(url_for('computer_management'))

    # If it's a GET request, display all computers
    computers = Computer.query.all()
    return render_template('computer_management.html', computers=computers, 
                           add_update_form=add_update_form, remove_form=remove_form)





######################
###  SECURITY SECTION ###
######################S



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





