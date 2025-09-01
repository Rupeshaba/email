from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app import db
from app.telegram import bp
from app.models import TelegramSettings
import requests

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Telegram message failed: {e}")
        return False

@bp.route('/')
@login_required
def index():
    settings = TelegramSettings.query.first()
    return render_template('telegram/index.html', title='Telegram Settings', settings=settings)

@bp.route('/configure', methods=['GET', 'POST'])
@login_required
def configure():
    settings = TelegramSettings.query.first()
    if request.method == 'POST':
        bot_token = request.form.get('bot_token')
        chat_id = request.form.get('chat_id')

        if not bot_token or not chat_id:
            flash('Bot Token and Chat ID are required.', 'danger')
            return redirect(url_for('telegram.configure'))

        if settings:
            settings.bot_token = bot_token
            settings.chat_id = chat_id
        else:
            settings = TelegramSettings(bot_token=bot_token, chat_id=chat_id)
            db.session.add(settings)
        db.session.commit()
        flash('Telegram settings saved successfully!', 'success')
        return redirect(url_for('telegram.index'))
    return render_template('telegram/configure.html', title='Configure Telegram', settings=settings)

@bp.route('/toggle_alerts', methods=['POST'])
@login_required
def toggle_alerts():
    settings = TelegramSettings.query.first()
    if settings:
        settings.alerts_enabled = not settings.alerts_enabled
        db.session.commit()
        flash(f'Telegram alerts {"enabled" if settings.alerts_enabled else "disabled"}.', 'success')
    else:
        flash('Telegram settings not found. Please configure them first.', 'danger')
    return redirect(url_for('telegram.index'))

@bp.route('/update_alert_preferences', methods=['POST'])
@login_required
def update_alert_preferences():
    settings = TelegramSettings.query.first()
    if settings:
        settings.alert_login_success = 'alert_login_success' in request.form
        settings.alert_login_failure = 'alert_login_failure' in request.form
        settings.alert_sending_started = 'alert_sending_started' in request.form
        settings.alert_sending_paused_resumed_stopped = 'alert_sending_paused_resumed_stopped' in request.form
        settings.alert_batch_sent = 'alert_batch_sent' in request.form
        settings.alert_errors = 'alert_errors' in request.form
        db.session.commit()
        flash('Telegram alert preferences updated.', 'success')
    else:
        flash('Telegram settings not found. Please configure them first.', 'danger')
    return redirect(url_for('telegram.index'))
