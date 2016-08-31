import os
from uuid import uuid4

#from mandrill import Mandrill
import sendgrid
from sendgrid.helpers.mail import *
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, redirect, abort

app = Flask(__name__)
cors = CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
sendgrid_client = sendgrid.SendGridAPIClient(apikey=os.environ['SENDGRID_API_KEY'])
db = SQLAlchemy(app)


class User(db.Model):

    def __init__(self, email):
        self.email = email
        self.uuid = str(uuid4())

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    uuid = db.Column(db.String(36), unique=True)


@app.route('/')
def index():
    return redirect('http://memeplatter.github.io/')


@app.route('/register', methods=['POST'])
def register():
    user = User.query.filter_by(email=request.form['email']).first()
    if user:
        return ('Email already registered', 403)
    user = User(request.form['email'])
    db.session.add(user)
    db.session.commit()
    return "Token: {}".format(user.uuid)


@app.route('/user/<uuid>', methods=['POST'])
def forward(uuid):
    user = User.query.filter_by(uuid=uuid).first()
    if not user:
        return ('User not found', 406)
    if len(request.form['email']) > 0:
        return ('Meme not found', 407)
    to_email = Email(user.email)
    from_email = Email(request.form['memail'])
    subject = request.form['subject']
    text = request.form['message']
    content = Content("text/plain", 'From: {}  \nSubject: {}  \n\nMessage Body:  \n{}'.format(request.form['name'], request.form['subject'], request.form['message']))
    #result = sendgrid_client.messages.send(message=message)
    mail = Mail(from_email, subject, to_email, content)
    response = sendgrid_client.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)
    #if result[0]['status'] != 'sent':
    #    abort(500)
    if 'next' in request.form:
        return redirect(request.form['next'])
    return response.status_code + '\n' + response.body + '\n' + response.headers


@app.errorhandler(400)
def bad_parameters(e):
    return ('<p>Missing information. Press the back button to complete '
            'the empty fields.</p><p><i>Developers: we were expecting '
            'the parameters "name", "email" and "message". You might '
            'also consider using JS validation.</i>', 400)


@app.errorhandler(500)
def error(e):
    return ('Sorry, something went wrong!', 500)
