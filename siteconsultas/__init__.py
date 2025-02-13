from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '50eadf27cea52c4d1c6ae5c02a55d503'

from siteconsultas import routes