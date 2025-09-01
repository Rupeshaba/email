import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import db
from app.models import SenderEmail, ReceiverEmail, MessageTemplate, LogEntry, Campaign
from datetime import datetime
import random
import time
import threading
from flask import current_app

def send_email_task_sync(receiver_id, campaign_id, app_instance, sender_id=None, retry_count=0):
    # This function will run in a separate thread
    with app_instance.app_context():
        receiver = ReceiverEmail.query.get(receiver_id)
        campaign = Campaign.query.get(campaign_id)
        template = MessageTemplate.query.get(campaign.template_id)

        if not receiver or not campaign or not template:
            log_event('ERROR', f"Failed to send email: Missing receiver, campaign or template. Receiver ID: {receiver_id}, Campaign ID: {campaign_id}", status='failure')
            return

        if receiver.status == 'sent':
            return # Already sent, skip

        sender = None
        if sender_id:
            sender = SenderEmail.query.get(sender_id)
        
        if not sender:
            # Rotate sender emails
            available_senders = SenderEmail.query.filter(
                SenderEmail.sent_count < SenderEmail.sending_limit
            ).all()
            if not available_senders:
                log_event('ERROR', "No available sender emails with remaining limits.", status='failure', receiver_email=receiver.email)
                receiver.status = 'failed'
                db.session.commit()
                return

            sender = random.choice(available_senders)

        try:
            # Personalize message (simple placeholder replacement)
            personalized_html_body = template.body_html.replace('{name}', receiver.email.split('@')[0]) # Example: use part before @ as name
            personalized_plain_body = template.body_plain.replace('{name}', receiver.email.split('@')[0]) if template.body_plain else None

            msg = MIMEMultipart('alternative')
            msg['From'] = sender.email
            msg['To'] = receiver.email
            msg['Subject'] = template.subject

            msg.attach(MIMEText(personalized_plain_body, 'plain'))
            msg.attach(MIMEText(personalized_html_body, 'html'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: # Example for Gmail
                smtp.login(sender.email, sender.password)
                smtp.send_message(msg)

            sender.sent_count += 1
            receiver.status = 'sent'
            receiver.sent_at = datetime.utcnow()
            campaign.emails_sent += 1
            db.session.commit()
            log_event('INFO', f"Email sent to {receiver.email} from {sender.email}", sender_email=sender.email, receiver_email=receiver.email, status='success')

        except Exception as e:
            db.session.rollback()
            error_message = str(e)
            log_event('ERROR', f"Failed to send email to {receiver.email} from {sender.email}: {error_message}", sender_email=sender.email, receiver_email=receiver.email, status='failure', error_reason=error_message)
            
            if retry_count < 3:
                # Retry after a delay in a new thread
                time.sleep(5 * (retry_count + 1)) # 5, 10, 15 seconds delay
                threading.Thread(target=send_email_task_sync, args=(receiver_id, campaign_id, app_instance, sender.id, retry_count + 1)).start()
            else:
                receiver.status = 'failed'
                campaign.emails_failed += 1
                db.session.commit()

# Helper to save logs (can be called from anywhere)
def log_event(level, message, sender_email=None, receiver_email=None, status=None, error_reason=None):
    log = LogEntry(level=level, message=message, sender_email=sender_email, receiver_email=receiver_email, status=status, error_reason=error_reason)
    db.session.add(log)
    db.session.commit()
