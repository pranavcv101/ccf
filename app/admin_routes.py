from flask import render_template,redirect,url_for,flash,request,jsonify
from app import app,db
from app.models import Users,Booking,Computer,History,CurrentBooking,Admin,Security,Configurations
from app.forms import LoginForm,AddUpdateComputerForm,RemoveComputerForm,ChangePasswordForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta,datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
from app.my_functions import hash_password,check_password,role_required


########################
###    AUTOMATION    ###
########################



def move_expired_bookings():
    with app.app_context():
        now = datetime.now()
        print("move_expired_bookings running")
        # Find expired bookings
        expired_bookings = Booking.query.filter((Booking.scheduled_datetime) <= now ).all()

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

@app.route("/admin_login", methods=['GET', 'POST'])
def admin_login_page():
    form = LoginForm()

    if form.validate_on_submit():
        # Fetch the admin user by username
        attempted_user = Admin.query.filter_by(username=form.rollno.data).first()

        # Check if the user exists and the password is correct
        if attempted_user and check_password(attempted_user.password_hash, form.password.data):
            login_user(attempted_user)
            flash(f'Successfully logged in as {attempted_user.username}', 'success')
            return redirect(url_for('admin_page'))  # Redirect after login
        else:
            flash('Login Unsuccessful. Check Username and Password', 'danger')

    return render_template("admin_login.html", form=form)


@app.route("/logout_admin")
# @login_required
# @role_required(['admin'])
def admin_logout_page():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("admin_login_page"))  # Redirect to admin login page


@app.route("/admin_home")
# @login_required
# @role_required(['admin'])
def admin_page():
    return render_template("admin_home.html")

@app.route("/students_details" , methods = ['GET' , 'POST'])
# @login_required
# @role_required(['admin'])
def student_details_page():
    students = Users.query.all()
    return render_template("students_details.html",students = students)


@app.route("/remove_student/<rollno>", methods=["POST"])
# @login_required
# @role_required(['admin'])
def remove_student(rollno):
    student = Users.query.filter_by(rollno=rollno).first()
    
    if student:
        # Move all bookings to history
        bookings = Booking.query.filter_by(user_rollno=rollno).all()
        for booking in bookings:
            history_entry = History(
                id=booking.id,
                user_rollno=booking.user_rollno,
                comp_id=booking.comp_id,
                created_at=booking.created_at,
                start_time=booking.start_time,
                end_time=booking.end_time,
                duration=booking.duration,
                status="Student removed"
            )
            db.session.add(history_entry)
            db.session.delete(booking)  # Remove from bookings table

        db.session.delete(student)  # Remove the student
        db.session.commit()
        return jsonify({"success": True})
    
    return jsonify({"success": False})



@app.route("/admin_home/booking_details")
# @login_required
# @role_required(['admin'])
def booking_details_page():
    # Fetch all booking records from the database
    bookings = Booking.query.all()
    return render_template("booking_details.html", bookings=bookings)

@app.route("/admin_home/booking_history")
# @login_required
# @role_required(['admin'])
def booking_history_page():
    # Fetch all booking records from the database
    bookings = History.query.all()
    return render_template("booking_history.html", bookings=bookings)

@app.route("/admin_home/current_bookings")
# @login_required
# @role_required(['admin'])
def current_bookings_page():
    # Fetch all booking records from the database
    bookings = CurrentBooking.query.all()
    return render_template("current_bookings.html", bookings=bookings)


@app.route('/cancel_a_booking/<int:booking_id>', methods=['POST'])
# @login_required
# @role_required(['admin'])
def cancel_a_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        # Move booking details to history
        history_entry = History(
            id = booking.id,
            user_rollno=booking.user_rollno,
            comp_id=booking.comp_id,
            created_at=booking.created_at,
            start_time=booking.start_time,
            end_time=booking.end_time,
            duration=booking.duration,
            status="Booking Removed"  # Setting status
        )

        db.session.add(history_entry)
        db.session.delete(booking)  # Remove from current bookings
        db.session.commit()

    return redirect(url_for('booking_details_page'))






@app.route('/admin_home/computers', methods=['GET', 'POST'])
# @login_required
# @role_required(['admin'])
def computer_management():
    add_update_form = AddUpdateComputerForm()
    remove_form = RemoveComputerForm()

    # Handle the add/update computer form submission
    if add_update_form.validate_on_submit():
        comp_id = add_update_form.comp_id.data
        status = add_update_form.status.data
        is_available = add_update_form.is_available.data == 'True'
        ip = add_update_form.ip.data
        existing_ip = Computer.query.filter_by(ip_address=ip).first()
        if existing_ip:
            flash("Error:IP already exists.", "danger")
        else:
            existing_computer = Computer.query.filter_by(comp_id=comp_id).first()
            
            if existing_computer:
                # Update the existing computer
                existing_computer.status = status
                existing_computer.is_available = is_available
                existing_computer.ip_address = ip
                db.session.commit()
                flash(f"Computer with ID {comp_id} has been updated successfully.", 'success')
            else:
                # Add a new computer
                new_computer = Computer(comp_id=comp_id, status=status, is_available=is_available,ip_address=ip)
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
# @login_required
# @role_required(['admin'])
def toggle_availability(comp_id):
    computer = Computer.query.get(comp_id)
    if computer:
        computer.is_available = not computer.is_available
        db.session.commit()
    return redirect(url_for('computer_management'))






@app.route('/configure', methods=['GET', 'POST'])
# @login_required
# @role_required(['admin'])
def configure_page():
    if request.method == 'POST':
        var_name = request.form.get('variable')
        new_value = request.form.get('new_value')

        if var_name:
            config_entry = Configurations.query.filter_by(variables=var_name).first()
            if config_entry:
                config_entry.values = new_value
                db.session.commit()
                flash(f"Updated {var_name} to {new_value}", "success")
            else:
                flash("Variable not found!", "danger")
        else:
            flash("Invalid input!", "warning")

    configurations = Configurations.query.all()
    return render_template('configure.html', configurations=configurations)

@app.route('/missbookers',methods = ['GET','POST'])
# @login_required
# @role_required(['admin'])
def missbookers_page():
    max_missed = int(Configurations.query.filter_by(variables="max_missed").first().values)
    miss_bookers = Users.query.filter(Users.bookings_missed > max_missed)
    return render_template('missbooking.html',miss_bookers = miss_bookers)

@app.route("/change_a_password", methods=["GET", "POST"])
def change_a_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data

        if new_password != confirm_password:
            flash("New and Confirm Password do not match!", "danger")
            return redirect(url_for("change_a_password"))

        # Fetch Admin and Security from database
        admin = Admin.query.first()
        security = Security.query.first()

        if not admin or not security:
            flash("Error: Admin or Security credentials not found!", "danger")
            return redirect(url_for("change_a_password"))

        # Verify old password with Admin's stored password
        if not check_password(admin.password_hash, old_password):
            flash("Incorrect Admin password!", "danger")
            return redirect(url_for("change_a_password"))

        # Update both Admin and Security passwords
        hashed_password = hash_password(new_password)
        admin.password_hash = hashed_password
        security.password_hash = hashed_password
        db.session.commit()

        flash("Admin & Security passwords updated successfully!", "success")
        return redirect(url_for("admin_page"))

    return render_template("change_a_password.html", form=form)

