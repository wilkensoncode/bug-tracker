import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, Blueprint, request, flash, redirect, url_for
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from sqlalchemy.orm import aliased
admin_view = Blueprint('admin_view', __name__)


def validate_credential(email=None, password=None):
    # pattern validate email
    validate_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    # validate pass
    validate_psswrd = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    if email and not password:
        return re.match(validate_email, email)
    elif password and not email:
        return re.match(validate_psswrd, password)


@admin_view.route('/admin')
def admin():
    if not current_user.is_authenticated:
        return redirect(url_for('admin_auth.adm_login'))
    if current_user.admin == True:
        return redirect('/admin/dashboard')
    else:
        flash("You are not authorize", category="error")
        return redirect(url_for('admin_auth.adm_login'))


@admin_view.route('/admin/dashboard')
def dashboard():
    from app import db
    from .models import Report, Developer, User, AssignTask, IssueStatus
    reports = Report.query.all()
    developers = (
        db.session
        .query(Developer, User.first_name, User.last_name)
        .join(User, User.email == Developer.email).all()
    )

    count_reports = len(reports)
    count_developers = len(developers)
    assigned = len(AssignTask.query.all())
    fixed = len(IssueStatus.query.filter_by(status="complete").all())

    if current_user.is_authenticated and current_user.admin == True:
        return render_template('adm_dash.html', fixed=fixed, assigned=assigned, reports=reports, developers=developers, count_reports=count_reports, count_dev=count_developers)
    else:
        flash("Most login to access this page", category="error")
        return redirect(url_for('admin_auth.adm_login'))


@admin_view.route('/admin/dev', methods=["GET", "POST"])
def add_dev():
    from .models import User, Developer
    from app import db
    current_date = datetime.now()
    new_date = current_date + timedelta(weeks=1)

    developer_alias = aliased(Developer)
    users = (
        db.session.query(User)
        .outerjoin(developer_alias, User.email == developer_alias.email)
        .filter(developer_alias.email.is_(None))
        .all()
    )

    if request.method == "POST":
        email = request.form.get("email")

        salary = request.form.get("salary")
        office = request.form.get("office")
        position = request.form.get("position")
        start_date = request.form.get("start_date")

        if not validate_credential(email, None):
            flash("Invalid Email", category="error")
        elif salary == '' or not salary.isdigit():
            flash("Invalid Salary", category="error")
        elif office == "":
            flash("Invalid office", category="error")
        elif position == '':
            flash("Invalid position", category="error")
        elif start_date == "":
            flash("Invalid start date", category="Error")
        else:
            from .models import Developer, User
            developer = Developer.query.filter_by(email=email).first()

            if not developer:
                new_dev = Developer(
                    email=email,
                    salary=salary,
                    office=office,
                    position=position,
                    start_date=start_date)

                db.session.add(new_dev)
                db.session.commit()
                flash("Developer added successfully", category="success")
            else:
                flash("Developer already exist", category="error")
    if current_user.is_authenticated and current_user.admin == True:
        return render_template('adm_add_dev.html', default_date=new_date.strftime("%Y-%m-%d"), users=users)
    else:
        flash("Most login to access this page", category="error")
        return redirect(url_for('admin_auth.adm_login'))


@admin_view.route('/admin/user-manage', methods=["GET", "POST"])
def update_info():
    if request.method == "POST":
        from .models import User, Update
        from app import db

        current_email = request.form.get("email")
        new_password = request.form.get("update_password")
        new_email = request.form.get("new_email")

        admin_password = request.form.get("admin_password")
        is_admin = request.form.get("is_admin")
        not_admin = request.form.get("not_admin")
        remove_user = request.form.get("remove_user")

        if current_user.admin == True:

            user = User.query.filter_by(email=current_email).first()
            if current_email and new_password and admin_password:
                if user:
                    if check_password_hash(current_user.password, admin_password):
                        user.password = generate_password_hash(
                            new_password, method='sha256')

                        update_info = Update(
                            affected_user_email=current_email,
                            admin_email=current_user.email,
                            operation="Update Password")

                        db.session.add(update_info)
                        db.session.commit()
                        flash("Password updated successfully",
                              category="success")
                    else:
                        flash("Invalid credentials", category="error")
                else:
                    flash("User does not exist", category="error")

            elif current_email and new_email and admin_password:
                if user:
                    if check_password_hash(current_user.password, admin_password):
                        user.email = new_email

                        update_info = Update(
                            affected_user_email=current_email,
                            admin_email=current_user.email,
                            operation="Update Email")

                        db.session.add(update_info)
                        db.session.commit()
                        flash("Email updated successfully", category="success")
                    else:
                        flash("Invalid credentials", category="error")
                else:
                    flash("User does not exist", category="error")

            elif current_email and is_admin and admin_password:
                if user:
                    if check_password_hash(current_user.password, admin_password):
                        user.admin = True
                        update_info = Update(
                            affected_user_email=current_email,
                            admin_email=current_user.email,
                            operation="Make user admin")

                        db.session.add(update_info)
                        db.session.commit()

                        flash("User is now an admin", category="success")
                    else:
                        flash("Invalid credentials", category="error")
                else:
                    flash("User does not exist", category="error")

            elif current_email and admin_password and not_admin and not is_admin and not new_email and not new_password:
                if user:
                    if check_password_hash(current_user.password, admin_password):
                        user.admin = False
                        update_info = Update(
                            affected_user_email=current_email,
                            admin_email=current_user.email,
                            operation="Remove admin privilege")

                        db.session.add(update_info)
                        db.session.commit()
                        flash("User is no longer an admin", category="success")
                    else:
                        flash("Invalid credentials", category="error")
                else:
                    flash("User does not exist", category="error")

            elif current_email and remove_user and admin_password and not not_admin and not is_admin and not new_email and not new_password:
                if user:
                    if check_password_hash(current_user.password, admin_password):
                        db.session.delete(user)

                        update_info = Update(
                            affected_user_email=current_email,
                            admin_email=current_user.email,
                            operation="Remove user")

                        db.session.add(update_info)
                        db.session.commit()
                        flash("User removed successfully", category="success")
                    else:
                        flash("Invalid credentials", category="error")
                else:
                    flash("User does not exist", category="error")
    if current_user.is_authenticated and current_user.admin == True:
        return render_template('user_manage.html')
    else:
        flash("Most login to access this page", category="error")
        return redirect(url_for('admin_auth.adm_login'))


@admin_view.route('/admin/task', methods=["GET", "POST"])
def task():
    from .models import Report, Developer, Update, User, AssignTask
    from app import db

    reports = Report.query.all()

    developers = (
        db.session
        .query(Developer, User.first_name, User.last_name)
        .join(User, User.email == Developer.email).all()
    )

    if request.method == "POST":

        bug_id = request.form.get('bug_id')
        dev_id = request.form.get('dev_id')
        priority = request.form.get('priority')

        if bug_id == '':
            flash("Bug ID cannot be empty", category="error")
        elif dev_id == '':
            flash("Dev ID cannot be empty", category="error")
        elif not priority:
            flash("Priority cannot be empty", category="error")
        else:

            dev = (Developer.query.filter_by(id=dev_id).first())

            report = Report.query.filter_by(id=bug_id).first()
            if dev:
                user = User.query.filter_by(email=dev.email).first()

            if dev and report:
                duplicate = AssignTask.query.filter_by(issueId=bug_id).first()
                if duplicate:
                    flash("Task already assigned", category="error")
                    return redirect(url_for('admin_view.task'))
                assign = AssignTask(
                    issueId=bug_id,
                    DeveloperId=dev_id,
                    userId=user.id,
                    priority=priority)

                report.assignedTo = user.id

                update_info = Update(
                    affected_user_email=dev.email,
                    admin_email=current_user.email,
                    operation=f"Assign Task issue{bug_id}")

                db.session.add(assign)
                db.session.add(update_info)
                db.session.commit()
                flash("Task assigned successfully", category="success")
            else:
                flash("Invalid IDs", category="error")
    if current_user.is_authenticated and current_user.admin == True:
        return render_template('adm_assign.html', reports=reports, developers=developers)
    else:
        flash("Most login to access this page", category="error")
        return redirect(url_for('admin_auth.adm_login'))
