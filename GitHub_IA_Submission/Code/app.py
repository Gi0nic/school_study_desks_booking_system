# This is app.py, this is the main file called.
from myproject import app
from flask import render_template
from flask_login import login_required, current_user

@app.route('/')
@login_required
def index():
    #if the user is an admin redirect to admin homepage
    if current_user.is_admin:
        return render_template("admins_home.html")
    #if the user is an student redirect to student homepage
    else:
        return render_template("students_home.html")

#start application
if __name__ == '__main__':
    app.run(debug=True)
