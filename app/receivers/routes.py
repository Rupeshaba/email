import io
import csv
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.receivers import bp
from app.models import ReceiverEmail, Campaign

@bp.route('/')
@login_required
def index():
    campaigns = Campaign.query.all()
    return render_template('receivers/index.html', title='Receiver Emails', campaigns=campaigns)

@bp.route('/manage/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def manage(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if request.method == 'POST':
        # Handle adding emails from textarea
        if 'emails_textarea' in request.form:
            emails_raw = request.form.get('emails_textarea')
            emails = [e.strip() for e in emails_raw.split('\n') if e.strip()]
            for email_address in emails:
                receiver = ReceiverEmail(email=email_address, campaign=campaign)
                db.session.add(receiver)
            campaign.total_emails += len(emails)
            db.session.commit()
            flash(f'{len(emails)} receiver emails added from textarea.', 'success')
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'danger')
            elif file and (file.filename.endswith('.txt') or file.filename.endswith('.csv')):
                stream = io.TextIOWrapper(file.stream, encoding='utf-8')
                new_emails_count = 0
                if file.filename.endswith('.csv'):
                    csv_reader = csv.reader(stream)
                    for row in csv_reader:
                        if row and row[0].strip(): # Assuming email is in the first column
                            receiver = ReceiverEmail(email=row[0].strip(), campaign=campaign)
                            db.session.add(receiver)
                            new_emails_count += 1
                else: # .txt file
                    for line in stream:
                        if line.strip():
                            receiver = ReceiverEmail(email=line.strip(), campaign=campaign)
                            db.session.add(receiver)
                            new_emails_count += 1
                campaign.total_emails += new_emails_count
                db.session.commit()
                flash(f'{new_emails_count} receiver emails added from file.', 'success')
            else:
                flash('Invalid file type. Please upload a .txt or .csv file.', 'danger')
        
        return redirect(url_for('receivers.manage', campaign_id=campaign.id))

    total_emails = campaign.receivers.count()
    sent_emails = campaign.receivers.filter_by(status='sent').count()
    pending_emails = campaign.receivers.filter_by(status='pending').count()
    failed_emails = campaign.receivers.filter_by(status='failed').count()

    return render_template('receivers/manage.html', 
                           title=f'Manage Receivers for {campaign.name}', 
                           campaign=campaign,
                           total_emails=total_emails,
                           sent_emails=sent_emails,
                           pending_emails=pending_emails,
                           failed_emails=failed_emails)

@bp.route('/edit_receiver/<int:receiver_id>', methods=['POST'])
@login_required
def edit_receiver(receiver_id):
    receiver = ReceiverEmail.query.get_or_404(receiver_id)
    campaign_id = receiver.campaign_id
    new_email = request.form.get('email')
    if new_email:
        receiver.email = new_email
        db.session.commit()
        flash('Receiver email updated.', 'success')
    else:
        flash('Email cannot be empty.', 'danger')
    return redirect(url_for('receivers.manage', campaign_id=campaign_id))

@bp.route('/delete_receiver/<int:receiver_id>', methods=['POST'])
@login_required
def delete_receiver(receiver_id):
    receiver = ReceiverEmail.query.get_or_404(receiver_id)
    campaign_id = receiver.campaign_id
    db.session.delete(receiver)
    campaign = Campaign.query.get(campaign_id)
    if campaign:
        campaign.total_emails -= 1
    db.session.commit()
    flash('Receiver email deleted.', 'success')
    return redirect(url_for('receivers.manage', campaign_id=campaign_id))

@bp.route('/create_campaign', methods=['POST'])
@login_required
def create_campaign():
    campaign_name = request.form.get('campaign_name')
    if campaign_name:
        campaign = Campaign(name=campaign_name)
        db.session.add(campaign)
        db.session.commit()
        flash(f'Campaign "{campaign_name}" created successfully!', 'success')
        return redirect(url_for('receivers.manage', campaign_id=campaign.id))
    flash('Campaign name cannot be empty.', 'danger')
    return redirect(url_for('receivers.index'))
