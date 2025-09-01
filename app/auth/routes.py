from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.auth import bp
from app.models import User
from werkzeug.security import generate_password_hash

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.first()

        if user is None:
            # If no user exists, create one with the provided password
            user = User(password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash('Admin user created. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        
        if user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid password', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
