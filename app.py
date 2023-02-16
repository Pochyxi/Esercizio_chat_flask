from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, join_room
from pymongo.errors import DuplicateKeyError
from forms import MessageForm

from user import User
from db import get_user, save_user, save_room, add_room_members, get_rooms_for_user, get_room, is_room_member, \
    get_room_members, save_message, get_message_by_room_id

app = Flask(__name__)
app.secret_key = 'My secret key'
socketio = SocketIO(app, cors_allowed_origins='*')
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    rooms = []
    if current_user.is_authenticated():
        rooms = get_rooms_for_user(current_user.username)
    return render_template('index.html', rooms=rooms)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = "Autenticazione fallita"
    return render_template('login.html', message=message)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_user(username, email, password)
            return redirect(url_for('home'))
        except DuplicateKeyError:
            message = "Username già esistente"
    return render_template('signup.html', message=message)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create-room/', methods=['GET', 'POST'])
@login_required
def create_room():
    message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [username.strip() for username in request.form.get('members').split(',')]

        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username)

            if current_user.username in usernames:
                usernames.remove(current_user.username)
                add_room_members(room_id, room_name, usernames, current_user.username)
                redirect(url_for('view_room', room_id=room_id))
            else:
                message = "Errore nella creazione della stanza"

    return render_template('create_room.html', message=message)


@app.route('/rooms/<room_id>/', methods=['GET', 'POST'])
@login_required
def view_room(room_id):
    message_form = MessageForm()
    room_messages = get_message_by_room_id(room_id)
    room_members = get_room_members(room_id)
    if request.method == 'POST':
        save_message(room_id, current_user.username, message_form.message.data)
        print("inserito messaggio con ", message_form.message.data)
        return redirect(url_for('view_room', room_id=room_id))

    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        return render_template('view_room.html',
                               username=current_user.username,
                               room=room,
                               room_members=room_members,
                               message_form=message_form,
                               room_messages=room_messages)
    else:
        return "Stanza non trovata", 404


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    socketio.run(app, debug=True)
