from flask import Flask
from flask_login import LoginManager

from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY')
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


from ChatAPP import routes


