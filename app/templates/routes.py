from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.templates import bp
from app.models import MessageTemplate

@bp.route('/')
@login_required
def index():
    templates = MessageTemplate.query.all()
    return render_template('templates/index.html', title='Message Templates', templates=templates)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        body_html = request.form.get('body_html')
        body_plain = request.form.get('body_plain')

        if not name or not subject or not body_html:
            flash('Name, Subject, and HTML Body are required.', 'danger')
            return redirect(url_for('templates.add'))

        template = MessageTemplate(name=name, subject=subject, body_html=body_html, body_plain=body_plain)
        db.session.add(template)
        db.session.commit()
        flash('Message template added successfully!', 'success')
        return redirect(url_for('templates.index'))
    return render_template('templates/add_edit.html', title='Add Message Template')

@bp.route('/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit(template_id):
    template = MessageTemplate.query.get_or_404(template_id)
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.subject = request.form.get('subject')
        template.body_html = request.form.get('body_html')
        template.body_plain = request.form.get('body_plain')
        db.session.commit()
        flash('Message template updated successfully!', 'success')
        return redirect(url_for('templates.index'))
    return render_template('templates/add_edit.html', title='Edit Message Template', template=template)

@bp.route('/delete/<int:template_id>', methods=['POST'])
@login_required
def delete(template_id):
    template = MessageTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    flash('Message template deleted successfully!', 'success')
    return redirect(url_for('templates.index'))

@bp.route('/set_active/<int:template_id>', methods=['POST'])
@login_required
def set_active(template_id):
    # Deactivate all other templates
    MessageTemplate.query.update({MessageTemplate.is_active: False})
    
    # Activate the selected template
    template = MessageTemplate.query.get_or_404(template_id)
    template.is_active = True
    db.session.commit()
    flash(f'Template "{template.name}" set as active.', 'success')
    return redirect(url_for('templates.index'))
