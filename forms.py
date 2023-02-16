from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class MessageForm(FlaskForm):
    message = StringField(label='inserisci messaggio', validators=[DataRequired()])
    submit = SubmitField(label='invia')
