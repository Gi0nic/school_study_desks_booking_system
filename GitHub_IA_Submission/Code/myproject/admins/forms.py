from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, TextAreaField
from wtforms.validators import DataRequired
from myproject.models import Desk

# Define a class for the form to add a desk, inheriting from FlaskForm
class AddForm(FlaskForm):
    # Define a string field for the name of the desk with required validation
    name = StringField('Name', validators=[DataRequired()])
    # Define a submit button for the form
    submit = SubmitField('Add Desk')
    
    # Define a custom validator for the name field
    def validate_name(self, field):
        # Check if a desk with the given name already exists in the database
        if Desk.query.filter_by(name=field.data).first():
            # Raise a validation error if the desk name already exists
            raise ValidationError('A desk with that name has been registered already')

# Define a class for a justification form, inheriting from FlaskForm
# This form is used for submitting a text area field for justifications
class JustificationForm(FlaskForm):
    # Define a text area field for the justification message with required validation
    message = TextAreaField('Justification', validators=[DataRequired()])

# Define a class for a ban form, inheriting from FlaskForm
# This form includes multiple submit buttons for different actions
class BanForm(FlaskForm):
    ban = SubmitField('Ban')  # Submit button to ban a user
    unban = SubmitField("Unban")  # Submit button to unban a user
    delete = SubmitField("Delete")  # Submit button to delete a user
    admin = SubmitField("False")  # Submit button to revoke admin status
    not_admin = SubmitField("True")  # Submit button to grant admin status

    