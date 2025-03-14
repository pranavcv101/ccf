from flask import render_template,redirect,url_for,flash,request,jsonify
from app import app,db
from app.models import Users,Booking,Computer,Lastbookedcomputer,History,CurrentBooking,Admin,Security,Configurations
from app.forms import StudentRegisterForm,LoginForm,BookingForm,AddUpdateComputerForm,RemoveComputerForm,SecurityForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta,datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time

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


