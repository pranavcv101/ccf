from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,IntegerField,DateTimeField,SelectField,RadioField
from wtforms.validators import DataRequired,Length,Email

class LoginForm(FlaskForm):
    rollno = StringField('Rollno', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3, max=128)])
    submit = SubmitField('Login')

class StudentRegisterForm(FlaskForm):
    rollno = StringField(label='Roll Number', validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=70)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=2, max=20)])
    batch = StringField('Batch',validators=[DataRequired()])
    YOP = StringField('Year of Passout',validators=[DataRequired()])
    submit = SubmitField('Register')

class BookingForm(FlaskForm):
    start_time = DateTimeField(
    'Start time',
    format='%Y-%m-%dT%H:%M',  # Match the datetime-local input format
    validators=[DataRequired()],
    render_kw={"type": "datetime-local"}  # Ensure correct HTML input type
    )
    duration = IntegerField('Duration (minutes)',validators=[DataRequired()])
    submit = SubmitField('Make Booking')

class AddUpdateComputerForm(FlaskForm):
    comp_id = StringField('Computer ID', validators=[DataRequired()])
    status = StringField('Status', validators=[DataRequired()])
    is_available = SelectField('Is Available', choices=[('True', 'Yes'), ('False', 'No')], validators=[DataRequired()])

class RemoveComputerForm(FlaskForm):
    comp_id = StringField('Computer ID', validators=[DataRequired()])

class SecurityForm(FlaskForm):
    rollno = StringField('Roll Number', validators=[DataRequired()])
    fetch_bookings=  SubmitField('Fetch bookings')
    booking = RadioField('Booking', choices=[(0, "No bookings selected")], coerce=int)
    Unlock =  SubmitField('Unlock computer')

