from flask import Blueprint, render_template

view = Blueprint('view', __name__)


@view.route('/')
def home():
    return render_template('index.html')


@view.route('/register')
def register():
    return render_template('register.html')


@view.route('/issues')
def issues():
    return render_template('issues.html')
