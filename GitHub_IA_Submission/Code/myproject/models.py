from myproject import db,login_manager
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from datetime import datetime, timedelta
# By inheriting the UserMixin we get access to a lot of built-in attributes
# which we will be able to call in our views!
# is_authenticated()
# is_active()
# is_anonymous()
# get_id()
# The user_loader decorator allows flask-login to load the current user
# and grab their id.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Defining the User model which inherits from UserMixin for authentication and db.Model for database operations
class User(UserMixin, db.Model):
    # Defining the database fields for the User model
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each user
    email = db.Column(db.String(256), unique=True)  # User's email, must be unique
    first_name = db.Column(db.String(64), index=True)  # User's first name
    second_name = db.Column(db.String(64), index=True)  # User's second name
    password_hash = db.Column(db.String(128))  # Hashed password for security
    is_banned = db.Column(db.Boolean, default=False)  # Flag to indicate if the user is banned
    bookings = db.relationship('Booking', backref='user')  # Relationship to the Booking model
    deletion_date = db.Column(db.Date)  # Date for scheduled deletion of the user
    is_admin = db.Column(db.Boolean, default=False)  # Flag to indicate if the user is an admin
    graduation_year = db.Column(db.Integer)  # User's graduation year

    # Method to schedule the user for deletion after a specified number of weeks
    def schedule_for_deletion(self, weeks=2):
        self.deletion_date = datetime.date.today() + datetime.timedelta(weeks=weeks)

    # Method to cancel the scheduled deletion of the user
    def cancel_deletion(self):
        self.deletion_date = None

    # Constructor for the User class
    def __init__(self, email, first_name, second_name, graduation_year, password):
        self.email = email
        self.first_name = first_name
        self.second_name = second_name
        self.graduation_year = graduation_year
        self.password_hash = generate_password_hash(password)  # Storing hashed password
        
    # Method to check if the provided password matches the stored hashed password
    def check_password(self, password):
        # Uses Werkzeug to check if the password hashes match
        return check_password_hash(self.password_hash, password)


# Define the Desk model for the database
class Desk(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the desk
    name = db.Column(db.String(256), unique=True)  # Unique name for the desk
    active = db.Column(db.Boolean, default=True)  # Boolean field to indicate if the desk is active
    deletion_date = db.Column(db.Date)  # Field to store the deletion date of the desk
    bookings = db.relationship('Booking', backref='desk')  # Establish a relationship to the Booking model
    
    # Constructor for the Desk class
    def __init__(self, name):
        self.name = name  # Initialize the desk with a name

# Define the Booking model for the database
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the booking
    deskid = db.Column(db.Integer, db.ForeignKey('desk.id'), nullable=False)  # Foreign key to the Desk model
    bookerId = db.Column(db.Integer, db.ForeignKey('user.id'))  # Foreign key to the User model
    date = db.Column(db.Date, nullable=False)  # Field to store the date of the booking
    period = db.Column(db.String(256))  # Field to store the period of the booking
