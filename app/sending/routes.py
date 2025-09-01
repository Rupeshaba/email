from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required
from app import db
from app.sending import bp
from app.models import Campaign, ReceiverEmail, MessageTemplate, SenderEmail, LogEntry, TelegramSettings
from app.email_utils import send_email_task_sync, log_event
from app.telegram.routes import send_telegram_message
from datetime import datetime
import threading
import time

# Dictionary to hold thread objects for campaigns (for potential pause/resume/stop logic)
campaign_threads = {}
# A simple flag to control sending state
sending_paused = {}
sending_stopped = {}

@bp.route('/')
@login_required
def index():
    campaigns = Campaign.query.all()
    return render_template('sending/index.html', title='Sending Controls', campaigns=campaigns)

@bp.route('/start_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def start_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    active_template = MessageTemplate.query.filter_by(is_active=True).first()

    if not active_template:
        flash('No active message template found. Please set one in Templates.', 'danger')
        return redirect(url_for('sending.index'))
    
    if not campaign.receivers.first():
        flash('No receiver emails in this campaign. Please add some first.', 'danger')
        return redirect(url_for('sending.index'))

    if not SenderEmail.query.first():
        flash('No sender emails configured. Please add at least one.', 'danger')
        return redirect(url_for('sending.index'))

    campaign.template_id = active_template.id
    campaign.status = 'running'
    campaign.started_at = datetime.utcnow()
    db.session.commit()

    log_event('INFO', f'Campaign "{campaign.name}" started.', status='started')
    telegram_settings = TelegramSettings.query.first()
    if telegram_settings and telegram_settings.alerts_enabled and telegram_settings.alert_sending_started:
        send_telegram_message(telegram_settings.bot_token, telegram_settings.chat_id, f'Campaign <b>"{campaign.name}"</b> started!')

    # Start sending in a new thread
    def _send_campaign_thread(campaign_id, app_instance):
        with app_instance.app_context():
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return

            sending_paused[campaign_id] = False
            sending_stopped[campaign_id] = False

            pending_receivers = campaign.receivers.filter_by(status='pending').all()
            for receiver in pending_receivers:
                if sending_stopped.get(campaign_id):
                    break
                while sending_paused.get(campaign_id):
                    time.sleep(1) # Wait if paused
                
                send_email_task_sync(receiver.id, campaign.id, app_instance)
                # Small delay to prevent overwhelming SMTP server and allow UI updates
                time.sleep(1) 
            
            # After loop, if not stopped, set to completed
            if not sending_stopped.get(campaign_id):
                campaign.status = 'completed'
                campaign.completed_at = datetime.utcnow()
                db.session.commit()
                log_event('INFO', f'Campaign "{campaign.name}" completed.', status='completed')
                telegram_settings = TelegramSettings.query.first()
                if telegram_settings and telegram_settings.alerts_enabled and telegram_settings.alert_sending_paused_resumed_stopped:
                    send_telegram_message(telegram_settings.bot_token, telegram_settings.chat_id, f'Campaign <b>"{campaign.name}"</b> completed!')

    thread = threading.Thread(target=_send_campaign_thread, args=(campaign.id, current_app._get_current_object()))
    thread.daemon = True # Allow main program to exit even if thread is running
    thread.start()
    campaign_threads[campaign.id] = thread # Store thread object if needed

    flash(f'Campaign "{campaign.name}" started successfully!', 'success')
    return redirect(url_for('sending.index'))

@bp.route('/pause_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def pause_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.status == 'running':
        campaign.status = 'paused'
        sending_paused[campaign_id] = True
        db.session.commit()
        log_event('INFO', f'Campaign "{campaign.name}" paused.', status='paused')
        telegram_settings = TelegramSettings.query.first()
        if telegram_settings and telegram_settings.alerts_enabled and telegram_settings.alert_sending_paused_resumed_stopped:
            send_telegram_message(telegram_settings.bot_token, telegram_settings.chat_id, f'Campaign <b>"{campaign.name}"</b> paused.')
        flash(f'Campaign "{campaign.name}" paused.', 'info')
    return redirect(url_for('sending.index'))

@bp.route('/resume_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def resume_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.status == 'paused':
        campaign.status = 'running'
        sending_paused[campaign_id] = False
        db.session.commit()
        log_event('INFO', f'Campaign "{campaign.name}" resumed.', status='resumed')
        telegram_settings = TelegramSettings.query.first()
        if telegram_settings and telegram_settings.alerts_enabled and telegram_settings.alert_sending_paused_resumed_stopped:
            send_telegram_message(telegram_settings.bot_token, telegram_settings.chat_id, f'Campaign <b>"{campaign.name}"</b> resumed!')
        
        flash(f'Campaign "{campaign.name}" resumed.', 'success')
    return redirect(url_for('sending.index'))

@bp.route('/stop_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def stop_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.status in ['running', 'paused']:
        campaign.status = 'stopped'
        sending_stopped[campaign_id] = True
        sending_paused[campaign_id] = False # Ensure it's not stuck in paused state
        campaign.completed_at = datetime.utcnow()
        db.session.commit()
        log_event('INFO', f'Campaign "{campaign.name}" stopped.', status='stopped')
        telegram_settings = TelegramSettings.query.first()
        if telegram_settings and telegram_settings.alerts_enabled and telegram_settings.alert_sending_paused_resumed_stopped:
            send_telegram_message(telegram_settings.bot_token, telegram_settings.chat_id, f'Campaign <b>"{campaign.name}"</b> stopped.')
        
        flash(f'Campaign "{campaign.name}" stopped.', 'info')
    return redirect(url_for('sending.index'))

@bp.route('/get_campaign_status/<int:campaign_id>')
@login_required
def get_campaign_status(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    total_emails = campaign.total_emails
    emails_sent = campaign.emails_sent
    emails_failed = campaign.emails_failed
    emails_pending = total_emails - emails_sent - emails_failed

    return jsonify({
        'status': campaign.status,
        'total_emails': total_emails,
        'emails_sent': emails_sent,
        'emails_failed': emails_failed,
        'emails_pending': emails_pending,
        'progress': (emails_sent / total_emails * 100) if total_emails > 0 else 0
    })
