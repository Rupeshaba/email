from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.settings import bp
from app.models import User
from werkzeug.security import generate_password_hash

@bp.route('/')
@login_required
def index():
    return render_template('settings/index.html', title='Settings')

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(old_password):
            flash('Incorrect old password.', 'danger')
            return redirect(url_for('settings.change_password'))
        
        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'danger')
            return redirect(url_for('settings.change_password'))
        
        if len(new_password) < 6: # Basic password strength check
            flash('New password must be at least 6 characters long.', 'danger')
            return redirect(url_for('settings.change_password'))

        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('settings.index'))
    return render_template('settings/change_password.html', title='Change Password')
