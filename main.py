"""
Run the concert times app, collecting the appropriate username from the URL

"""

from flask import Flask
from concert_times import *


# Call the get_rdio_ewconcerts function based on the URL
app = Flask(__name__)
@app.route('/<username>')
def get_username(username):
    print("What is happening.")
    return get_rdio_ewconcerts(username)
@app.route('/')
def hello():
    return "Did you forget your username?"