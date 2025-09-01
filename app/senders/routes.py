from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.senders import bp
from app.models import SenderEmail

@bp.route('/')
@login_required
def index():
    senders = SenderEmail.query.all()
    return render_template('senders/index.html', title='Sender Emails', senders=senders)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        sending_limit = request.form.get('sending_limit', type=int)

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('senders.add'))

        sender = SenderEmail(email=email, password=password, sending_limit=sending_limit)
        db.session.add(sender)
        db.session.commit()
        flash('Sender email added successfully!', 'success')
        return redirect(url_for('senders.index'))
    return render_template('senders/add_edit.html', title='Add Sender Email')

@bp.route('/edit/<int:sender_id>', methods=['GET', 'POST'])
@login_required
def edit(sender_id):
    sender = SenderEmail.query.get_or_404(sender_id)
    if request.method == 'POST':
        sender.email = request.form.get('email')
        new_password = request.form.get('password')
        sender.sending_limit = request.form.get('sending_limit', type=int)

        if new_password:
            sender.password = new_password # Setter will encrypt

        db.session.commit()
        flash('Sender email updated successfully!', 'success')
        return redirect(url_for('senders.index'))
    return render_template('senders/add_edit.html', title='Edit Sender Email', sender=sender)

@bp.route('/delete/<int:sender_id>', methods=['POST'])
@login_required
def delete(sender_id):
    sender = SenderEmail.query.get_or_404(sender_id)
    db.session.delete(sender)
    db.session.commit()
    flash('Sender email deleted successfully!', 'success')
    return redirect(url_for('senders.index'))
