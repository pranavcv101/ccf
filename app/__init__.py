from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample.db' 
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///psqlsample.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:psql_sample_password@localhost:5432/ccf_db'
app.config['SECRET_KEY'] = 'ec9439cfc6c796ae2029594x'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.app_context().push()  #to avoid error when creating that database from terminal

bcrypt= Bcrypt(app)

# Initialize LoginManager
login_manager = LoginManager() 
login_manager.init_app(app)
login_manager.login_view = 'student_login_page'  # This is the view where the user is redirected if not logged in
login_manager.login_message_category = 'info'  # Flash message category for login-required messages

#importing routes for flask to identify routes and other stuff  
from app import admin_routes
from app import student_routes
from app import security_routes
from app import models
