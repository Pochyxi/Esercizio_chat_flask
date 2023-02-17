from flask_login import current_user, login_user, login_required, logout_user
from flask import redirect, url_for, render_template, request
from pymongo.errors import DuplicateKeyError

from ChatAPP import app, login_manager
from ChatAPP.db import get_rooms_for_user, save_user, get_user, save_room, add_room_members, get_room, is_room_admin, \
    get_message_by_room_id, get_room_members, save_message, is_room_member, update_room, remove_room_members
from ChatAPP.forms import MessageForm


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


@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [member['_id']['username'] for member in get_room_members(room_id)]
        room_members_str = ",".join(existing_room_members)

        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            room['name'] = room_name
            update_room(room_id, room_name)

            new_members = [username.strip() for username in request.form.get('members').split(',')]

            members_to_add = set(new_members) - set(existing_room_members)
            members_to_remove = list(set(existing_room_members) - set(new_members))

            if len(members_to_add):
                add_room_members(room_id, room_name, members_to_add, current_user.username)

            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)
            message = 'Stanza modificata con successo'
            room_members_str = ",".join(new_members)
            room['name'] = get_room(room_id)
            return redirect(url_for('view_room', room_id=room_id))

        room_members_str = ",".join(existing_room_members)
        return render_template('edit_room.html', room=room, room_members_str=room_members_str, message=message)
    else:
        return "Stanza non trovata", 404


@app.route('/rooms/<room_id>/', methods=['GET', 'POST'])
@login_required
def view_room(room_id):
    room = get_room(room_id)
    message_form = MessageForm()
    room_messages = get_message_by_room_id(room_id)
    room_messages_length = len(room_messages)
    room_members = get_room_members(room_id)
    if request.method == 'POST':
        save_message(room_id, current_user.username, message_form.message.data)
        print("inserito messaggio con ", message_form.message.data)
        return redirect(url_for('view_room', room_id=room_id))

    if room and is_room_member(room_id, current_user.username):
        return render_template('view_room.html',
                               username=current_user.username,
                               current_user=current_user,
                               room=room,
                               room_members=room_members,
                               message_form=message_form,
                               room_messages=room_messages,
                               room_messages_length=room_messages_length)
    else:
        return "Stanza non trovata", 404


@login_manager.user_loader
def load_user(username):
    return get_user(username)
