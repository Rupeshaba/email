import csv
from io import StringIO
from flask import render_template, Response, request
from flask_login import login_required
from app import db
from app.dashboard import bp
from app.models import LogEntry, SenderEmail, Campaign, ReceiverEmail
from sqlalchemy import func

@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    total_sent = LogEntry.query.filter_by(status='success').count()
    total_failed = LogEntry.query.filter_by(status='failure').count()
    total_pending = ReceiverEmail.query.filter_by(status='pending').count()

    sender_stats = db.session.query(
        SenderEmail.email,
        SenderEmail.sent_count,
        SenderEmail.sending_limit
    ).all()

    campaign_stats = db.session.query(
        Campaign.name,
        Campaign.status,
        Campaign.total_emails,
        Campaign.emails_sent,
        Campaign.emails_failed
    ).all()

    # Logs with filters
    logs = LogEntry.query.order_by(LogEntry.timestamp.desc())

    filter_status = request.args.get('status')
    filter_sender = request.args.get('sender')
    filter_receiver = request.args.get('receiver')

    if filter_status and filter_status != 'all':
        logs = logs.filter_by(status=filter_status)
    if filter_sender:
        logs = logs.filter(LogEntry.sender_email.ilike(f'%{filter_sender}%'))
    if filter_receiver:
        logs = logs.filter(LogEntry.receiver_email.ilike(f'%{filter_receiver}%'))
    
    logs = logs.limit(100).all() # Limit to last 100 logs for dashboard display

    return render_template('dashboard.html', 
                           title='Dashboard',
                           total_sent=total_sent,
                           total_failed=total_failed,
                           total_pending=total_pending,
                           sender_stats=sender_stats,
                           campaign_stats=campaign_stats,
                           logs=logs,
                           filter_status=filter_status,
                           filter_sender=filter_sender,
                           filter_receiver=filter_receiver)

@bp.route('/export_logs')
@login_required
def export_logs():
    si = StringIO()
    cw = csv.writer(si)

    headers = ['Timestamp', 'Level', 'Message', 'Sender Email', 'Receiver Email', 'Status', 'Error Reason']
    cw.writerow(headers)

    logs = LogEntry.query.order_by(LogEntry.timestamp.asc()).all()
    for log in logs:
        cw.writerow([
            log.timestamp.isoformat(),
            log.level,
            log.message,
            log.sender_email,
            log.receiver_email,
            log.status,
            log.error_reason
        ])
    
    output = si.getvalue()
    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=email_marketing_logs.csv'
    return response

@bp.route('/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    try:
        num_deleted = db.session.query(LogEntry).delete()
        db.session.commit()
        flash(f'{num_deleted} log entries cleared successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing logs: {str(e)}', 'danger')
    return redirect(url_for('dashboard.dashboard'))
