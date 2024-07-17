from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField, HiddenField
from wtforms.validators import DataRequired
from datetime import datetime, timedelta

# Define a class for the booking form, inheriting from FlaskForm
class BookingForm(FlaskForm):
    # Define a date field for selecting the date of the booking
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    # Define a select field for choosing the booking period
    # This field has predefined choices for different periods during the day
    period = SelectField('Period', 
                         choices=[('Period 1', 'Period 1'), ('Period 2', 'Period 2'), 
                                  ('Morning Break', 'Morning Break'), ('Period 3', 'Period 3'), 
                                  ('Period 4', 'Period 4'), ('Lunch', 'Lunch'), 
                                  ('Period 5', 'Period 5'), ('Period 6', 'Period 6')],
                         validators=[DataRequired()])
    # Define a submit button for the form
    submit = SubmitField('Book')
    
# Define a class for the select desk form, inheriting from FlaskForm
# This is a simple form with just a submit button for selecting a desk
class SelectDeskForm(FlaskForm):
    submit = SubmitField('Select')

# Define a class for the delete booking form, inheriting from FlaskForm
# This form includes a submit button to delete a booking
class DeleteBookingForm(FlaskForm):
    delete = SubmitField('Delete')



