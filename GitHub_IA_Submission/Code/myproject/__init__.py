import os
from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_apscheduler import APScheduler
from datetime import datetime

app = Flask(__name__)

# Create a login manager object
login_manager = LoginManager()

# Often people will also separate these into a separate config.py file 
app.config['SECRET_KEY'] = 'mysecretkey'
basedir = os.path.abspath(os.path.dirname(__file__))
# connecting sqlalchemy to MYSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://db_manager:ciao@localhost/db_booking'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Migrate(app,db)

from myproject.models import User, Desk

# We can now pass in our app to the login manager
login_manager.init_app(app)

# Tell users what view to go to when they need to login.
login_manager.login_view = "login.login"

# after creating the Flask app
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# NOTE! These imports need to come after you've defined db, otherwise you will
# get errors in your models.py files.
## Grab the blueprints from the other views.py files for each "app"

# Route for the student's home page
@app.route('/students_home')
def students_home():
    return render_template("students_home.html")  # Render the student's home page template

# Route for the admin's home page
@app.route('/admin_home')
def admins_home():
    if current_user.is_admin:  # Check if the current user is an admin
        return render_template("admins_home.html")  # Render the admin's home page template if they are an admin
    else:
        flash("Only admins can access this page")  # Show a message if the user is not an admin
        return redirect(url_for('students_home'))  # Redirect non-admin users to the student's home page

# Scheduled task for deleting desks that got deleted from admins
@scheduler.task('cron', id='delete_old_desks', hour='0')  # Schedule the task to run at midnight
def delete_old_desks():
    #relates schedule session to the app
    with app.app_context ():
        # Query for desks with a deletion date that is past or equal to the current datetime
        old_desks = Desk.query.filter(Desk.deletion_date <= datetime.utcnow()).all()
        for desk in old_desks:  # Iterate through the old desks
            db.session.delete(desk)  # Delete each old desk
        db.session.commit()  # Commit the changes to the database

# Scheduled task for deleting students who got deleted from admins
@scheduler.task('cron', id='delete_old_users', hour='0')
def delete_old_users():
    #relates schedule session to the app
    with app.app_context():
        old_users = User.query.filter(User.deletion_date <= datetime.utcnow()).all() #seelect users with a deletion date past the current date
        for user in old_users: #iterate through the old users
            db.session.delete(user) #delete each user
        db.session.commit() #committing the changes to the database

# Scheduled task for deleting graduated users based on graduation year
@scheduler.task('cron', id='delete_old_users', hour='0', minute='0')  # Schedule the task to run at midnight
def delete_graduated_users():
    #relates schedule session to the app
    with app.app_context():
        current_year = datetime.now().year  # Get the current year
        current_month = datetime.now().month  # Get the current month

        # Determine the old users based on the current month and year
        if current_month > 6:  # If the current month is after June
            # Select users who graduated in the current year or earlier
            old_users = User.query.filter((User.graduation_year < current_year) | 
                                        (User.graduation_year == current_year)).all()
        else:
            # Select users who graduated in the previous years
            old_users = User.query.filter(User.graduation_year < current_year).all()

        for user in old_users:  # Iterate through the old users
            db.session.delete(user)  # Delete each old user

        db.session.commit()  # Commit the changes to the database

    
from myproject.students.views import students_blueprint
from myproject.admins.views import admins_blueprint
from myproject.login.views import login_blueprint

app.register_blueprint(admins_blueprint,url_prefix="/admins")
app.register_blueprint(students_blueprint,url_prefix='/students')
app.register_blueprint(login_blueprint, url_prefix="/login")
