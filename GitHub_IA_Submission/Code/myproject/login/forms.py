from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError, IntegerField, SelectField
from wtforms.validators import DataRequired,Email,EqualTo
from myproject.models import User
from datetime import datetime

# Define a class for the login form, inheriting from FlaskForm
class LoginForm(FlaskForm):
    # Define a string field for email with required validation and email format validation
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Define a password field with required validation
    password = PasswordField('Password', validators=[DataRequired()])
    # Define a submit button for the form
    submit = SubmitField('Log In')

# Define a class for the registration form, inheriting from FlaskForm
class RegistrationForm(FlaskForm):
    # Define a string field for email with required validation and email format validation
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Define a string field for first name with required validation
    first_name = StringField('first_name', validators=[DataRequired()])
    # Define a string field for second name with required validation
    second_name = StringField('second_name', validators=[DataRequired()])
    # Define a password field with required validation and a validation to ensure it matches the confirmation password
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm', message='Passwords Must Match!')])
    # Define a password field for confirming the password with required validation
    pass_confirm = PasswordField('Confirm password', validators=[DataRequired()])
    # Define a select field for graduation date with required validation, choices are to be populated dynamically
    graduation_year = SelectField('Graduation Year', choices=[], validators=[DataRequired()])
    # Define a submit button for the form
    submit = SubmitField('Register!')

    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)  # Call the constructor of the parent class (FlaskForm)

        # Determine the current year and month
        current_year = datetime.now().year  # Get the current year
        current_month = datetime.now().month  # Get the current month
    
            # Based on the current month, decide which years to show as options
        if current_month <= 6:  # If the current month is June or earlier
            # Offer the current year and the next three years as options
            years = [current_year, current_year+1, current_year+2, current_year+3]
        else:  # If the current month is later than June
            # Offer the next year and the following three years as options
            years = [current_year+1, current_year+2, current_year+3, current_year+4]
    
        # Update the choices for the graduation_date field
        self.graduation_year.choices = [(str(year), str(year)) for year in years]  # Convert years to string for the SelectField

    def validate_email(self, field):
        # Custom validation for the email field
        # Check if there is a user registered with the same email
        if User.query.filter_by(email=field.data).first():
            # If a user with the same email exists, raise a validation error
            raise ValidationError('Your email has been registered already!')
    
        # Check if the email belongs to the School community
        if "@school_name.com" not in field.data:
            # If the email does not include the school domain, raise a validation error
            raise ValidationError("Your email needs to be part of the school community")


# Define a class for the verification form, inheriting from FlaskForm
class VerificationForm(FlaskForm):
    # Define an integer field for the verification code, requiring it to be filled out
    code = IntegerField('Verification Code', validators=[DataRequired()])
    # Define a submit button for the form
    submit = SubmitField('Verify')

# Define a class for the forgot password form, inheriting from FlaskForm
class ForgotPasswordForm(FlaskForm):
    # Define a string field for email with required validation and email format validation
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Define a submit button to request a password reset
    submit = SubmitField('Request Password Reset')
    
# Define a class for the reset password form, inheriting from FlaskForm
class ResetPasswordForm(FlaskForm):
    # Define a password field with required validation
    password = PasswordField('Password', validators=[DataRequired()])
    # Define a second password field for password confirmation
    # This field must be equal to the first password field
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    # Define a submit button to request the password reset
    submit = SubmitField('Request Password Reset')
