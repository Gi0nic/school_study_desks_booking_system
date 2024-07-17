from myproject import app, db
from flask import render_template, redirect, request, url_for, flash, abort, Blueprint, session
from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from myproject.models import User
from myproject.login.forms import LoginForm, RegistrationForm, VerificationForm, ForgotPasswordForm, ResetPasswordForm
from sqlalchemy.orm.exc import NoResultFound
from flask_sqlalchemy import SQLAlchemy
from myproject import db, login_manager
from random import randint
from myproject.email_service import send_email
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

# Blueprint for the login-related routes
login_blueprint = Blueprint('login', __name__, template_folder='templates/login')

# Route for logging out
@login_blueprint.route('/logout')
@login_required  # Ensures that only logged-in users can access this route
def logout():
    logout_user()  # Logs out the current user
    flash('You logged out!')  # Shows a message to the user indicating they have logged out
    return redirect(url_for('login.login'))  # Redirects the user to the login page

# Route for handling login
@login_blueprint.route('/login', methods=['GET', 'POST'])  # Defines route for login, handling both GET and POST requests
def login():
    form = LoginForm()  # Creates an instance of the login form

    if form.validate_on_submit():  # Checks if the form is submitted and valid
        # Attempt to find the user by their email
        user = User.query.filter_by(email=form.email.data).first()  # Queries the database for the user by email

        try:
            # Verify the password and check if user is not banned
            if user.check_password(form.password.data) and user is not None and not user.is_banned:
                login_user(user)  # Logs in the user
                flash('Logged in successfully.')  # Shows success message

                # Redirect to the next page or to the index page
                next = request.args.get('next')  # Retrieves the 'next' parameter from the URL, if available
                if next == None or not next[0] == '/':  # Checks if 'next' is not set or invalid
                    next = url_for('index')  # Sets 'next' to the index page if it's invalid
                return redirect(next)  # Redirects to the 'next' page or index page
            elif user.is_banned:
                flash("Your account has been banned, please contact the school board")  # Shows a ban message if the user is banned
                return render_template('login.html', form=form)  # Renders the login page again with the form    
            else:
                flash("Password is wrong")  # Shows an error message if the password is incorrect
        except:
            flash("Email is wrong")  # Shows an error message if there is an issue with the email (like not found in DB)
    return render_template('login.html', form=form)  # Renders the login page with the form

# Route for handling registration
@login_blueprint.route('/register', methods=['GET', 'POST'])  # Defines the route for registration, handling both GET and POST requests
def register():
    form = RegistrationForm()  # Creates an instance of the registration form

    if form.validate_on_submit():  # Checks if the form is submitted and valid
        # Create a new User record with the submitted details
        user = User(email=form.email.data, 
                    first_name=form.first_name.data, 
                    second_name=form.second_name.data,
                    graduation_year=form.graduation_year.data, 
                    password=form.password.data)

        # Generate a random 4-digit code for email verification
        code = randint(1000, 9999)

        # Store the verification code and user details in the session
        session['verification_code'] = code
        session['user'] = {
            'email': form.email.data,
            'first_name': form.first_name.data,
            'second_name': form.second_name.data,
            'graduation_year': form.graduation_year.data,
            'password': form.password.data
        }

        # Send a verification email with the generated code
        send_email(subject="Email Verification", 
                   sender="Desksbookingsystem@gmail.com", 
                   recipients=[form.email.data], 
                   text_body=f"Your verification code is: {code}")

        flash('Verification code has been sent to your email!', 'info')  # Show a message to the user
        return redirect(url_for('login.verify'))  # Redirect to the verification page
    return render_template('register.html', form=form)  # Render the registration form

# Route for verification after registration
@login_blueprint.route('/verify', methods=['GET', 'POST'])  # Defines the route for verification, handling both GET and POST requests
def verify():
    form = VerificationForm()  # Creates an instance of the verification form

    if form.validate_on_submit():  # Checks if the form is submitted and valid
        if session['verification_code'] == form.code.data:  # Compares the submitted code with the code stored in session
            # Create and commit new user to the database
            user = User(**session['user'])  # Unpacks user details from the session and creates a new User object
            db.session.add(user)  # Adds the new user to the database session
            db.session.commit()  # Commits the session, saving changes to the database

            flash('Thanks for registering! Now you can login!', 'success')  # Show a success message
            return redirect(url_for('login.login'))  # Redirect to the login page
        else:
            flash('Wrong verification code. Please try again.', 'danger')  # Show an error message for incorrect code
    return render_template('verify.html', form=form)  # Render the verification form

# Route for handling forgot password
@login_blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()  # Instantiate the forgot password form
    if form.validate_on_submit():  # Check if the form is valid on submission
        # Find user by email
        user = User.query.filter_by(email=form.email.data).first()  # Query the database for user with the provided email
        if user:
            # Generate a unique token for password reset
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')  # Serialize the user's email into a token

            # Send email with password reset link
            url_with_token = url_for('login.reset_password', token=token, _external=True)  # Generate a URL with the token for resetting the password
            send_email('Reset Your Password', 
                       sender="Desksbookingsystem@gmail.com", 
                       recipients=[user.email], 
                       text_body=f'Dear {user.email} this is the link to reset your password: {url_with_token}')  # Send the reset email
            flash('A password reset link has been sent to {}.'.format(user.email))  # Notify the user about the sent link
        else:
            # If no user found with the given email
            flash('Email not found.')  # Notify that the email was not found
        return redirect(url_for('login.login'))  # Redirect to the login page
    return render_template('forgot_password.html', form=form)  # Render the forgot password form

# Route for resetting password using the token
@login_blueprint.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        # Attempt to load the email from the token
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # Deserialize the token to obtain the email, valid for 1 hour
    except:
        # If token is invalid or expired
        flash('The password reset link is invalid or has expired.')  # Notify the user if the token is invalid or expired
        return redirect(url_for('login.login'))  # Redirect to the login page

    form = ResetPasswordForm()  # Instantiate the reset password form
    if form.validate_on_submit():  # Check if the form is valid on submission
        # Find the user by email
        user = User.query.filter_by(email=email).first()  # Query the database for the user with the provided email
        if user:
            # Update the user's password
            user.password_hash = generate_password_hash(form.password.data)  # Hash and update the user's new password
            db.session.commit()  # Commit the changes to the database
            flash('Your password has been reset.')  # Notify the user that their password has been reset
            return redirect(url_for('login.login'))  # Redirect to the login page
    return render_template('reset_password.html', form=form)  # Render the reset password form

