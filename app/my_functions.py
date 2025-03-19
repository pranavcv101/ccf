from flask import redirect,url_for,flash
from app import db
from app.models import Booking,Computer,Configurations
from flask_login import current_user
from datetime import timedelta,datetime
from functools import wraps

from flask_bcrypt import Bcrypt


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

def round_robin_assignment(start_time,duration_m):
    # Retrieve last booked computer
    #last_booked = Lastbookedcomputer.query.first()  # Get the last booked computer
    last_booked_entry = Configurations.query.filter_by(variables="last_booked").first()
    lb = last_booked_entry.values if last_booked_entry else None

    # Get the comp_id of the last booked computer
    #last_booked_comp_id = last_booked.comp_id if last_booked else None

    # Get all available computers
    computers = Computer.query.filter_by(is_available=True).all()
    print("==>> All available computers are", computers)

    # If no computers are available, return None
    if not computers:
        return None

    # Start from the last booked computer and check availability in circular manner
    start_index = next((index for index, comp in enumerate(computers) if comp.comp_id == lb), -1) + 1
    
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
            #last_booked.comp_id = selected_computer.comp_id
            if last_booked_entry:
                last_booked_entry.values = selected_computer.comp_id  # Update existing entry
            else:
                new_entry = Configurations(variables="last_booked", values=selected_computer.comp_id)
                db.session.add(new_entry)  # Insert new entry if missing
            db.session.commit()
            return selected_computer

    # If no computer is available after a full cycle, return None
    return None


def conflict_check(start_time, end_time):
    existing_booking = Booking.query.filter(Booking.user_rollno == current_user.rollno).all()
    for booking in existing_booking:
        booking_end_time = booking.end_time
        if (booking.start_time <= start_time < booking_end_time) or \
           (booking.start_time < end_time <= booking_end_time):
            print("conflict return true")
            return True  # Conflict found
    print("conflict returns false")
    return False  # No conflict found



def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "danger") 

                # Redirect to the appropriate login page based on the role
                if "admin" in allowed_roles:
                    return redirect(url_for("admin_login_page"))  # Ensure this route exists
                elif "security" in allowed_roles:
                    return redirect(url_for("security_login_page"))  # If applicable
                else:
                    return redirect(url_for("student_login_page"))  # Redirect to student login by default


            return f(*args, **kwargs)
        return decorated_function
    return decorator


def time_check(start_time):
    """Checks if the booking start time is in the past."""
    if start_time < datetime.now():
        return False
    return True

bcrypt = Bcrypt()

def hash_password(plain_text_password):
    return bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

def check_password(hashed_password, attempted_password):
    return bcrypt.check_password_hash(hashed_password, attempted_password)

