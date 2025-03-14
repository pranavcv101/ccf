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








######################
###  ADMIN SECTION ###
######################

@app.route("/admin_login",methods = ['GET' , 'POST'])
def admin_login_page():
    form = LoginForm()
    if form.validate_on_submit(): 
        # Add authentication logic (check if rollNo and password are valid)
        attempted_user = Admin.query.filter_by(username=form.rollno.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):  # You should hash passwords in real scenario
            login_user(attempted_user)
            flash(f'Successfully logged in as {attempted_user.username}', 'success')
            return redirect(url_for('admin_page'))  # Redirect after login
        else:
            flash('Login Unsuccessful. Check Roll No and password', 'danger')
    return render_template("admin_login.html" ,form = form)

@app.route("/admin_home")
def admin_page():
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

@app.route('/cancel_a_booking/<int:booking_id>', methods=['POST'])
def cancel_a_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        db.session.delete(booking)
        db.session.commit()
    return redirect(url_for('booking_details_page'))






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

@app.route('/toggle_availability/<comp_id>', methods=['POST'])
def toggle_availability(comp_id):
    computer = Computer.query.get(comp_id)
    if computer:
        computer.is_available = not computer.is_available
        db.session.commit()
    return redirect(url_for('computer_management'))




@app.route('/password_management')
def password_management():
    return render_template('password_management.html')


@app.route('/configure', methods=['GET', 'POST'])
def configure_page():
    if request.method == 'POST':
        var_name = request.form.get('variable')
        new_value = request.form.get('new_value')

        if var_name and new_value.isdigit():
            config_entry = Configurations.query.filter_by(variables=var_name).first()
            if config_entry:
                config_entry.values = int(new_value)
                db.session.commit()
                flash(f"Updated {var_name} to {new_value}", "success")
            else:
                flash("Variable not found!", "danger")
        else:
            flash("Invalid input!", "warning")

    configurations = Configurations.query.all()
    return render_template('configure.html', configurations=configurations)


