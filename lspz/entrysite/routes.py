
from flask import Flask, render_template

from .. import log
from .app import app
from .music_collection import MusicLibrary

from .api import bp as api_bp

@app.route("/")
def index():
    return render_template('index.html')

app.register_blueprint(api_bp)
