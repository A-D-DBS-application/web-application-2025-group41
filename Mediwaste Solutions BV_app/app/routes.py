from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint
from functools import wraps



# Create the Blueprint object
main = Blueprint('main', __name__, url_prefix='/')
# Homepage route
@main.route('/')
def index():
    return render_template('Homepage.html')

# Register route
@main.route('/register')
def register():
    return render_template('Register.html')

# Forgot password route
@main.route('/forgot-password')
def forgot_password():
    return render_template('ForgotPassword.html')

# Login route
@main.route('/login')
def login():
    return render_template('Login.html')

# Authentication decorator for protected routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Dashboard route (protected page - we'll discuss authentication later)
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('Dashboard.html')

# Input route
@main.route('/input')
@login_required
def input_page():
    return render_template('Input.html')

# Output route
@main.route('/output')
@login_required
def output():
    return render_template('Output.html')
