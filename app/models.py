from app import db,login_manager,bcrypt
from flask_login import UserMixin
# Required by Flask-Login to load a user from the session
# @login_manager.user_loader
# def load_user(user_id):
#     return Users.query.get(user_id)


@login_manager.user_loader
def load_user(user_id):
    # Try loading from Users table
    user = Users.query.get(user_id)
    if user:
        return user  # Return user if found

    # Try loading from Admins table
    admin = Admin.query.get(user_id)
    if admin:
        return admin  # Return admin if found
    
    security = Security.query.get(user_id)
    if security:
        return security


class Users(db.Model, UserMixin):
    rollno = db.Column(db.String(20), primary_key=True)  # Roll number, unique for each user and primary key
    name = db.Column(db.String(80), nullable=False)  # Name of the user
    phone = db.Column(db.String(15), nullable=False)  # Phone number
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email, must be unique
    password_hash = db.Column(db.Text, nullable=False)  # Password for authentication
    batch = db.Column(db.String(20))
    year_of_passout = db.Column(db.Integer)
    no_of_bookings = db.Column(db.Integer, default=0)  # Count of bookings made by the user
    bookings_missed = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20),default="student")
    #remeber we used to have an id attribute user mixin used to take that default , but now since we dont have it we have to use this fucntionn
    def get_id(self):
        return self.rollno




class Admin(db.Model,UserMixin):
    __tablename__ = 'admin'
    username = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20),default="admin")


    def get_id(self):
        return self.username

# SECURITY Table
class Security(db.Model,UserMixin):
    __tablename__ = 'security'
    username = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20),default="security")


    def get_id(self):
        return self.username

    # @property
    # def password(self):
    #     return self.password

    # @password.setter
    # def password(self, plain_text_password):
    #     self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    # def check_password_correction(self, attempted_password):
    #     return bcrypt.check_password_hash(self.password_hash, attempted_password)


class Computer(db.Model):
    comp_id = db.Column(db.String(20), primary_key=True)  # Unique computer ID and primary key
    status = db.Column(db.String(20), nullable=False)  # Status of the computer (e.g., "available", "booked", "offline")
    is_available = db.Column(db.Boolean, default=True)  # Binary column for availability (True = available, False = not available)
    no_of_times_booked = db.Column(db.Integer, default=0)
    ip_address = db.Column(db.String(50),default = "not assigned")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique booking ID
    user_rollno = db.Column(db.String(20), db.ForeignKey('users.rollno'), nullable=False)  # User who made the booking
    comp_id = db.Column(db.String(20), db.ForeignKey('computer.comp_id'), nullable=False)  # Computer being booked
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # When the booking was made
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration of the booking in minutes
    

    # Relationships
    user = db.relationship('Users', backref=db.backref('bookings', lazy=True))
    computer = db.relationship('Computer', backref=db.backref('bookings', lazy=True))

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique history entry ID
    user_rollno = db.Column(db.String(20), db.ForeignKey('users.rollno'), nullable=False)  # User who made the booking
    comp_id = db.Column(db.String(20), db.ForeignKey('computer.comp_id'), nullable=False)  # Computer that was booked
    created_at = db.Column(db.DateTime)  # When the booking was made
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30))
    


class CurrentBooking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True)  # Unique booking ID
    user_rollno = db.Column(db.String(20), db.ForeignKey('users.rollno'), nullable=False)  # User who made the booking
    comp_id = db.Column(db.String(20), db.ForeignKey('computer.comp_id'), nullable=False)  # Computer being booked
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # When the booking was made
    start_time = db.Column(db.DateTime, nullable=False)  # Booking start time
    end_time = db.Column(db.DateTime, nullable=False)  # Booking end time
    duration = db.Column(db.Integer, nullable=False)  # Duration of the booking in minutes
    otp = db.Column(db.Integer,nullable = False)
    ip_address = db.Column(db.String(20),nullable = False)

    # Relationships
    user = db.relationship('Users', backref=db.backref('current_bookings', lazy=True))
    computer = db.relationship('Computer', backref=db.backref('current_bookings', lazy=True))

class Configurations(db.Model):
    variables = db.Column(db.String(20),primary_key = True)
    values = db.Column(db.String(20),nullable = False)

##########DUMMY VALUES FOR TABLES GIVEN BELOW################
'''
Configurations
insert into configurations values ('min_duration','10'),('max_duration','200'),('lastbooked','COM001'),('max_bookings','10'),('max_missed','10');

'''
'''
insertion for admin and security 
ccf_db=# insert into admin values ('admin1','$2b$12$bBX6dyGN6JkMp8Z3051a0.5H90gYp5yNNUVFAD4Ix0yMjb7IIpfnu','admin');
INSERT 0 1
ccf_db=# insert into security values ('security1','$2b$12$bBX6dyGN6JkMp8Z3051a0.5H90gYp5yNNUVFAD4Ix0yMjb7IIpfnu','security');
'''