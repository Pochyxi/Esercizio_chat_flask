# ### MODULI ### #
from flask_login import current_user, login_user, login_required, logout_user
from flask import redirect, url_for, render_template, request
from pymongo.errors import DuplicateKeyError

# ###  IMPORTS PACKAGE ### #
from ChatAPP import app, login_manager
from ChatAPP.db import get_rooms_for_user, save_user, get_user, save_room, add_room_members, get_room, is_room_admin, \
    get_message_by_room_id, get_room_members, save_message, is_room_member, update_room, remove_room_members
from ChatAPP.forms import MessageForm, CupidoForm


# ### CONTROLLO SE L'UTENTE E' AUTENTICATO ### #
################################################
def check_auth():
    if current_user.is_authenticated:
        return True
    return False


# ### PAGINA PER IL LOGIN ### #
###############################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        if request.form.get('username') and request.form.get('password'):
            username = request.form.get('username')
            password_input = request.form.get('password')
            user = get_user(username)

            if user and user.check_password(password_input):
                login_user(user)
                return redirect(url_for('home'))
            else:
                message = "Autenticazione fallita"
        else:
            message = "Non puoi lasciare i campi vuoti"

        if request.form.get('registrati') == 'registrati':
            # pass # do something else
            print("registrati")
            return redirect(url_for('signup'))

    return render_template('login.html', message=message)


# ### PAGINA DI REGISTRAZIONE  ### #
####################################
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        if request.form.get('username') and request.form.get('email') and request.form.get('password'):
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            try:
                save_user(username, email, password)
                return redirect(url_for('home'))
            except DuplicateKeyError:
                message = "Username già esistente"
        else:
            message = 'Non lasciare i campi vuoti'
    return render_template('signup.html', message=message)


# ### ROTTA PER IL LOGOUT  ### #
################################
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# ### PAGINA PRINCIPALE ### #
#############################
@app.route('/', methods=['GET', 'POST'])
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    rooms = []
    if current_user.is_authenticated():
        rooms = get_rooms_for_user(current_user.username)
        print(rooms)

    if request.method == 'POST':
        if request.form.get('logout') == 'logout':
            # pass # do something else
            print("logout")
            return redirect(url_for('logout'))
        elif request.form.get('add_room') == 'add_room':
            return redirect(url_for('create_room'))
        elif request.form.get('leave_room'):
            room_id = request.form.get('leave_room')
            # l'utente sceglie di uscire dalla room
            # c'è il metodo remove_room_members che ci permette di eliminare da una stanza un membro
            # parametri necessari, l'id della room e lo username
            # controlliamo che l'utente sia effettivamente un membro della stanza
            flag_member = is_room_member(room_id, current_user.username)
            print("flag_member ------> ", flag_member)
            print("room_id ------> ", room_id)
            member_to_delete = [current_user.username]
            print(member_to_delete)
            if flag_member == 1:
                remove_room_members(room_id, member_to_delete)
                return redirect(url_for('home'))
    return render_template('index.html', rooms=rooms, check_auth=check_auth())


# ### CREAZIONE DELLA STANZA ### #
##################################
@app.route('/create-room/', methods=['GET', 'POST'])
@login_required
def create_room():
    message = ''
    if request.method == 'POST':
        if request.form.get('room_name'):
            room_name = request.form.get('room_name')
            usernames = [username.strip() for username in request.form.get('members').split(',')]

            if len(room_name) and len(usernames):
                room_id = save_room(room_name, current_user.username)

                if current_user.username in usernames:
                    usernames.remove(current_user.username)
                    add_room_members(room_id, room_name, usernames, current_user.username)

            return redirect(url_for('home'))
        else:
            message = "Errore nella creazione della stanza"

    return render_template('create_room.html', message=message, check_auth=check_auth())


# ### MODIFICA DELLA STANZA  ### #
##################################
@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [member['_id']['username'] for member in get_room_members(room_id)]
        room_members_str = ",".join(existing_room_members)

        message = ''
        if request.method == 'POST':
            if request.form.get('room_name') and request.form.get('members'):
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

            elif request.form.get('go_home') == 'home':
                return redirect(url_for('home'))

        room_members_str = ",".join(existing_room_members)

        return render_template('edit_room.html',
                               room=room,
                               room_members_str=room_members_str,
                               message=message,
                               check_auth=check_auth())
    else:
        return "Stanza non trovata", 404


# ### PAGINA DELLA CHAT ### #
#############################
@app.route('/rooms/<room_id>/', methods=['GET', 'POST'])
@login_required
def view_room(room_id):
    room = get_room(room_id)
    message_form = MessageForm()
    cupido_form = CupidoForm()
    room_messages = get_message_by_room_id(room_id)
    room_messages_length = len(room_messages)
    room_members = get_room_members(room_id)
    check_room_admin = is_room_admin(room_id, current_user.username)
    love_message = ''

    if request.method == 'POST':

        if request.form.get('message_input'):
            save_message(room_id, current_user.username, message_form.message.data)
            print("inserito messaggio con ", message_form.message.data)
            return redirect(url_for('view_room', room_id=room_id))
        elif request.form.get('modifica_stanza') == 'Modifica stanza':
            print(request.path)
            return redirect(request.path + "/edit")
            # ritornare la rotta attuale più /edit
        elif request.form.get('go_home') == 'home':
            return redirect(url_for('home'))
        elif request.form.get('cupido') == 'cupido':
            love_message = 'Ti voglio bene by Adi ♥'

    if room and is_room_member(room_id, current_user.username):
        return render_template('view_room.html',
                               username=current_user.username,
                               current_user=current_user,
                               room=room,
                               room_members=room_members,
                               message_form=message_form,
                               room_messages=room_messages,
                               room_messages_length=room_messages_length,
                               check_room_admin=check_room_admin,
                               check_auth=check_auth(),
                               cupido_form=cupido_form,
                               love_message=love_message)
    else:
        return "Stanza non trovata", 404


@login_manager.user_loader
def load_user(username):
    return get_user(username)
