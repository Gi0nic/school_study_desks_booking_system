from flask import Blueprint,render_template,redirect,url_for, flash, request
from sqlalchemy import desc
from datetime import datetime, timedelta, date
from myproject import db, app
from flask_login import current_user, login_required
from myproject.students.forms import BookingForm, SelectDeskForm, DeleteBookingForm
from myproject.models import Desk, Booking
from myproject.email_service import send_email


# Create a Flask Blueprint for the 'students' section of the application
students_blueprint = Blueprint('students',
                              __name__,
                              template_folder='templates/students')  # Set the directory for the templates

# Define a route for selecting a desk
@students_blueprint.route('/select_desk', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in to access this route
def select_desk():
    desks = Desk.query.filter_by(active=True).all()  # Retrieve all active desks from the database
    form = SelectDeskForm()  # Instantiate the select desk form

    # Check if the form is submitted and valid
    if form.validate_on_submit():
        desk_id = request.form.get('desk_id')  # Get the selected desk id from the form
        # Redirect to the book desk route with the selected desk id
        return redirect(url_for('students.book_desk', desk_id=desk_id))
    
    # Render the select desk template with the list of desks and the form
    return render_template('select_desk.html', desks=desks, form=form)
    

# Route for students to book a desk
@students_blueprint.route('/book/<int:desk_id>', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in to access this route
def book_desk(desk_id):
    desk = Desk.query.get(desk_id)  # Retrieve the desk by its ID
    if not desk:
        flash('Desk not found')  # Show a message if the desk is not found
        return redirect(url_for('students_home'))  # Redirect to the students' home page
    
    # Calculate the date two weeks ago from today
    two_weeks_ago = datetime.today().date() - timedelta(weeks=2)
    # Count the number of bookings made by the current user in the last two weeks
    user_bookings = Booking.query.filter(Booking.bookerId==current_user.id, Booking.date>=two_weeks_ago).count()

    if user_bookings >= 5:
        flash('You have reached the maximum limit of 5 bookings in two weeks')  # Show a limit reached message
        return redirect(url_for('students_home'))  # Redirect to the students' home page
    
    form = BookingForm()  # Instantiate the booking form
    if form.validate_on_submit():  # Check if the form is valid on submission
        # Validate booking conditions (no weekends, within the next 2 weeks, and no double booking)
        if form.date.data.weekday() > 4:
            flash('Cannot book on weekends')
        elif form.date.data < date.today() or form.date.data > date.today() + timedelta(weeks=2):
            flash('You can only book for the next 2 weeks')
        elif Booking.query.filter_by(deskid=desk.id, date=form.date.data, period=form.period.data).first():
            flash('This desk is already booked for the selected time')
        else:
            # Create and save the new booking
            booking = Booking(deskid=desk.id, bookerId=current_user.id, date=form.date.data, period=form.period.data)
            db.session.add(booking)  # Add the new booking to the database session
            db.session.commit()  # Commit the session to save changes to the database
            flash('Desk booked successfully, you can delete it at any time in the "manage bookings" section')  # Show a success message
            # Send a confirmation email to the user about the successful booking
            send_email(subject="Desk booking confirmation",
                       sender="Desksbookingsystem@gmail.com",
                       recipients=[current_user.email],
                       text_body=f"Dear {current_user.first_name}, we confirm that your booking for desk {booking.desk.name} in date {booking.date} {booking.period} was successful")
            return redirect(url_for('students_home'))  # Redirect to the students' home page
    
    # Render the book desk template with the form and desk details
    return render_template("book_desk.html", form=form, desk=desk)


# Route for students to view and manage their bookings
@students_blueprint.route('/mybookings', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in to access this route
def my_bookings():
    form = DeleteBookingForm()  # Instantiate the form for deleting bookings
    
    # Check if the request is a POST request
    if request.method == 'POST':
        # Validate the form and check if the delete button was pressed
        if form.validate_on_submit() and form.delete.data:
            booking_id = request.form.get('booking_id')  # Get the booking ID from the form
            # Retrieve the booking from the database
            booking_to_delete = Booking.query.get(booking_id)
            # Check if the booking exists, belongs to the current user, and is in the future
            if booking_to_delete and booking_to_delete.bookerId == current_user.id and booking_to_delete.date >= date.today():
                db.session.delete(booking_to_delete)  # Delete the booking from the database
                db.session.commit()  # Commit the changes to the database
                flash('Booking deleted successfully!', 'success')  # Show a success message
                # Send a confirmation email to the user about the deletion
                send_email(subject="Desk booking deletion",
                           sender="Desksbookingsystem@gmail.com",
                           recipients=[current_user.email],
                           text_body=f"Dear {current_user.first_name}, we confirm that your booking was deleted succesfully")
                return redirect(url_for('students.my_bookings'))  # Redirect back to the my bookings page
        
        flash('Cannot delete this booking!', 'danger')  # Show an error message if the booking can't be deleted

    # Query for past bookings (bookings with a date before today)
    past_bookings = Booking.query.filter(Booking.bookerId == current_user.id, Booking.date < date.today()).order_by(desc(Booking.date)).all()
    # Query for upcoming bookings (bookings with a date from today onwards)
    upcoming_bookings = Booking.query.filter(Booking.bookerId == current_user.id, Booking.date >= date.today()).order_by(Booking.date).all()

    # Render the my bookings template with the bookings data and the form
    return render_template('mybookings.html', past_bookings=past_bookings, upcoming_bookings=upcoming_bookings, form=form)

