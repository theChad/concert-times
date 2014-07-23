"""
Run the concert times app, collecting the appropriate username from the URL

"""

from flask import Flask
from flask import request
from concert_times import *


# Call the get_rdio_ewconcerts function based on the URL
app = Flask(__name__)
@app.route('/<username>')
def get_username(username):
    return get_rdio_ewconcerts(username)
@app.route('/')
def hello():
    return get_rdio_lastfm_concerts(request.args.get("user"), request.args.get("city"))