from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy import desc, or_
from myproject import db, app
from myproject.models import Desk, Booking, User
from myproject.admins.forms import AddForm
from myproject.email_service import send_email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_login import current_user, login_required
from myproject.students.forms import DeleteBookingForm
from myproject.admins.forms import JustificationForm, BanForm
from datetime import datetime, timedelta, date

# Create a Blueprint for admin-related routes
admins_blueprint = Blueprint('admins', __name__, template_folder='templates/admins')

# Route to display the desks homepage, accessible only by admins
@admins_blueprint.route('/desks_home', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in to access this route
def desks_home():
    if current_user.is_admin:  # Check if the current user is an admin
        return render_template('desks_home.html')  # Render the desks homepage template for admins
    else:
        flash("Only admins can access this page")  # Show a message if the user is not an admin
        return redirect(url_for('students_home'))  # Redirect non-admins to the students' home page

# Route to add new desks, accessible only by admins
@admins_blueprint.route('/add_desks', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in to access this route
def add_desks():
    if current_user.is_admin:  # Check if the current user is an admin
        form = AddForm()  # Instantiate the form for adding desks
        if form.validate_on_submit():  # Check if the form submission is valid
            desk = Desk(name=form.name.data)  # Create a new Desk object with the name provided in the form
            db.session.add(desk)  # Add the new desk to the database session
            db.session.commit()  # Commit the session to save changes to the database
            flash('Successfully added the desk')  # Show a success message
            return redirect(url_for('admins.add_desks'))  # Redirect to the add desks page
        return render_template('add_desks.html', form=form)  # Render the template for adding desks
    else:
        flash("Only admins can access this page")  # Show a message if the user is not an admin
        return redirect(url_for('students_home'))  # Redirect non-admins to the students' home page

# Route for managing desks, accessible only by admins
@admins_blueprint.route('/manage_desks', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in to access this route
def manage_desks():
    if current_user.is_admin:  # Check if the current user is an admin
        desks = Desk.query.filter(Desk.deletion_date == None).all()  # Retrieve all desks that are not marked as deleted
        return render_template('manage_desks.html', desks=desks)  # Render the manage desks template with the list of desks
    else:
        flash("Only admins can access this page")  # Show a message if the user is not an admin
        return redirect(url_for('students_home'))  # Redirect non-admins to the students' home page

# Route to deactivate a desk, accessible only by admins
@admins_blueprint.route('/deactivate/<int:id>', methods=['POST'])
@login_required  # Require the user to be logged in to access this route
def deactivate_desk(id):
    desk = Desk.query.get(id)  # Retrieve the desk by its ID
    if desk:
        desk.active = False  # Set the desk's active status to False (deactivated)
        db.session.commit()  # Commit the session to save changes to the database
        flash('Desk deactivated successfully.')  # Show a success message
    return redirect(url_for('admins.manage_desks'))  # Redirect to the manage desks page


# Route to activate a desk, accessible only by admins
@admins_blueprint.route('/activate/<int:id>', methods=['POST'])
@login_required  # Require the user to be logged in to access this route
def activate_desk(id):
    desk = Desk.query.get(id)  # Retrieve the desk by its ID
    if desk:
        desk.active = True  # Set the desk's active status to True (activated)
        db.session.commit()  # Commit the session to save changes to the database
        flash('Desk activated successfully.')  # Show a success message
    return redirect(url_for('admins.manage_desks'))  # Redirect to the manage desks page

# Route to delete a desk, accessible only by admins
@admins_blueprint.route('/delete_desk/<desk_id>', methods=['POST'])
@login_required  # Require the user to be logged in to access this route
def delete_desk(desk_id):
    desk = Desk.query.get(desk_id)  # Retrieve the desk by its ID
    if desk:
        desk.active = False  # Set the desk's active status to False (deactivating it)
        desk.deletion_date = datetime.utcnow() + timedelta(weeks=4)  # Set the deletion date to 4 weeks from the current time
        db.session.commit()  # Commit the session to save changes to the database
        flash("Desk deleted successfully")  # Show a success message
    return redirect(url_for('admins.manage_desks'))  # Redirect to the manage desks page



@admins_blueprint.route('/bookings', methods=['GET', 'POST'])
@login_required
def bookings():
    # Check if the current user is an administrator
    if current_user.is_admin:
        # Retrieve the search query parameter, if provided
        search = request.args.get('search')
        # Instantiate the form for deleting bookings
        form = DeleteBookingForm()

        # Handle the submission of the delete booking form
        if form.validate_on_submit() and form.delete.data:
            # Retrieve the ID of the booking to be deleted from the form
            booking_id = request.form.get('booking_id')
            
            # Query the database for the booking using the provided ID
            booking_to_delete = Booking.query.get(booking_id)

            # Retrieve the justification message for deleting the booking
            justification_message = request.form.get("justification")
            # Send an email notification to the user about the booking deletion
            send_email(
                subject="Desk booking deletion",
                sender=current_user.email,
                recipients=[booking_to_delete.user.email],
                text_body=f"Dear {booking_to_delete.user.first_name}, your booking for desk '{booking_to_delete.desk.name}' on {booking_to_delete.date} for {booking_to_delete.period} was cancelled because: {justification_message}. If you think this is a mistake please contact the school board.")

            # Delete the booking from the database
            db.session.delete(booking_to_delete)
            # Commit the changes to the database
            db.session.commit()
            
            # Show a success message to the admin
            flash('Booking deleted successfully!', 'success')
            # Redirect to the bookings management page
            return redirect(url_for('admins.bookings'))

        # Prepare the base query for retrieving bookings
        base_query = Booking.query

        # If a search term was provided, modify the query to include a filter
        if search:
            # Format the search string for partial matching
            search = "%{}%".format(search)
            # Adjust the query to filter bookings based on the search term
            base_query = base_query.join(Booking.user, Booking.desk)\
                .filter(or_(User.first_name.ilike(search), User.second_name.ilike(search), Desk.name.ilike(search)))

        # Retrieve past bookings from the database, ordered by date, and store it in an array
        past_bookings = Booking.query.filter(Booking.date < date.today()).order_by(desc(Booking.date)).all()
        # Retrieve past bookings from the database, ordered by date, and store it in an array
        upcoming_bookings = Booking.query.filter(Booking.date >= date.today()).order_by(Booking.date).all()
        # Render the bookings page with the retrieved data and the form
        return render_template('bookings.html', past_bookings=past_bookings, upcoming_bookings=upcoming_bookings, form=form)
    else:
        # Display a message if a non-admin tries to access this page and redirect them
        flash("Only admins can access this page")
        return redirect(url_for('students_home'))


# Route to manage user accounts, accessible only by admins
@admins_blueprint.route('/manage_accounts', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in to access this route
def manage_accounts():
    if current_user.is_admin:  # Check if the current user is an admin
        search = request.args.get('search')  # Get the search parameter from the URL if any
        now = datetime.utcnow()  # Get the current datetime
        # Query to fetch all users except the admin and the current user, and those not marked for deletion
        users = User.query.filter(User.email != "admin@school_name.com").filter(User.deletion_date == None).filter(User.email != current_user.email).all()    
        form = BanForm()  # Instantiate the BanForm

        # Filter users based on the search query
        if search:
            users = users.filter(or_(User.email.contains(search), User.first_name.contains(search), User.second_name.contains(search)))
        
        # Process form submission
        if form.validate_on_submit():
            user_id = request.form.get("user_id")  # Get the user_id from the form
            action = request.form.get("action")  # Get the action (ban, delete, admin) from the form
            user = User.query.get(user_id)  # Retrieve the user by ID

            # Ban or unban the user
            if user and action == "ban":
                user.is_banned = not user.is_banned  # Toggle the is_banned status of the user
                db.session.commit()  # Commit the changes to the database
                # Notify the user via flash message and email about the ban status
                if user.is_banned:
                    justification = request.form.get("justification")
                    flash(f"{user.first_name} {user.second_name} was banned successfully")
                    send_email(subject="Desk booking account banned",
                        sender=current_user.email,
                        recipients=[user.email],
                        text_body=f"Dear {user.first_name} your account of the desk booking system was banned because: {justification}. If you think this is a mistake please contact the school board.")
                else:
                    flash(f"{user.first_name}{user.second_name} was disbanned successfully")
                    send_email(subject="Desk booking account disbanned",
                        sender=current_user.email,
                        recipients=[user.email],
                        text_body=f"Dear {user.first_name} your account of the desk booking system was disbanned. You will now be able to login again.")
                return redirect(url_for('admins.manage_accounts'))

            # Mark the user for deletion
            elif user and action == "delete":
                delete_date = now + timedelta(weeks=2)
                user.deletion_date = delete_date  # Set the deletion date to 2 weeks from now
                db.session.commit()  # Commit the changes to the database
                # Notify the user via flash message and email about the deletion schedule
                flash(f"{user.first_name} {user.second_name} will be deleted on {delete_date.strftime('%Y-%m-%d')}")
                send_email(subject="Desk booking account deletion notice",
                    sender=current_user.email,
                    recipients=[user.email],
                    text_body=f"Dear {user.first_name}, your account of the desk booking system will be deleted on {delete_date.strftime('%Y-%m-%d')}. If you think this is a mistake please contact the school board.")
            
            # Toggle the admin status of the user
            elif user and action == "admin":
                user.is_admin = not user.is_admin  # Toggle the is_admin status of the user
                db.session.commit()  # Commit the changes to the database
                return redirect(url_for('admins.manage_accounts'))

        # Render the manage accounts template with the necessary data
        return render_template('manage_accounts.html', users=users, form=form, today=date.today())
    else:
        flash("Only admins can access this page")  # Show a message if the user is not an admin
        return redirect(url_for('students_home'))  # Redirect non-admins to the students' home page


# Function to get the list of graduation years
def get_graduation_years():
    current_year = datetime.now().year  # Get the current year
    # Determine the graduation years based on the current month
    if datetime.now().month <= 6:
        # If it's the first half of the year, include the current year and the next three years
        return [current_year, current_year+1, current_year+2, current_year+3]
    else:
        # If it's the second half of the year, include the next four years starting from the next year
        return [current_year+1, current_year+2, current_year+3, current_year+4]

# Route to display statistics, accessible via the admins blueprint
@admins_blueprint.route('/statistics')
def statistics():
    years = get_graduation_years()  # Get the list of graduation years
    desks = Desk.query.all()  # Query all desks from the database
    
    # Get total bookings per graduation year
    total_bookings = {
        year: Booking.query.join(User).filter(User.graduation_year == year).count()
        for year in years
    }

    # Get bookings per desk per graduation year
    desk_bookings = {}
    for desk in desks:
        key = (desk.id, desk.name)  # Create a tuple key consisting of desk id and name
        # For each desk, calculate the number of bookings per graduation year
        desk_bookings[key] = {
            year: Booking.query.join(User).filter(User.graduation_year == year, Booking.deskid == desk.id).count()
            for year in years
        }
    
    # Render the statistics template with the required data
    return render_template('statistics.html', years=years, total_bookings=total_bookings, desk_bookings=desk_bookings)
