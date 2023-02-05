from flask import Flask, render_template

from .app import app

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/data/track/<mbid>")
def get_track_by_mbid(mbid):
    return {
        "mbid": mbid,
    }
