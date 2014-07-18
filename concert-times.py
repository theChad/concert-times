import os
from flask import Flask
from rauth import OAuth1Service
import urllib.parse, requests
import re

def get_rdio_artists(username):
    """Get all the artists in username's Rdio collection"""
    # Create Rdio OAuth object 
    rdio = OAuth1Service(
        name='Rdio',
        consumer_key=os.environ['RDIO_KEY'],
        consumer_secret=os.environ['RDIO_SECRET'],
        request_token_url='http://api.rdio.com/oauth/request_token',
        access_token_url='http://api.rdio.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authorize',
        base_url='http://api.rdio.com/1/')
    
    #Open a signed, unathorized Rdio session
    session = rdio.get_session()
    #Get the Rdio user key
    params = urllib.parse.urlencode({'method': 'findUser', 'vanityName': username})
    findUser_result = session.post('',data = params)
    userKey = findUser_result.json()['result']['key']
    #Collect all Rdio artists
    params = urllib.parse.urlencode({'method': 'getArtistsInCollection', 'user': userKey})
    artists_result = session.post('', data = params)
    if artists_result.json()['status'] == 'ok':
        artists = {x['name'] for x in artists_result.json()['result']}
    return artists

def get_all_concerts():
    """Return a dictionary of all concerts on the Early Warnings page, indexed by artist."""
    #Parse Early Warning concerts
    chicagoReader = requests.get('http://www.chicagoreader.com/chicago/EarlyWarnings')
    reader_html = chicagoReader.text
    ew_artists_spots = [m.start() for m in re.finditer('<li class="l0 event">', reader_html)]
    ew_artists_spots.append(ew_artists_spots[1]-ew_artists_spots[0]+\
                            ew_artists_spots[len(ew_artists_spots)-1])
    ew_artists = {}
    
    for i in range(len(ew_artists_spots)-1):
        raw_data = reader_html[ew_artists_spots[i]:ew_artists_spots[i+1]]
        artist_concert_info = [x for x in re.split('<[^>]+>\s*',raw_data) if not x=='']
        current_artists = artist_concert_info[0].split(',')
        for artist in current_artists:
            ew_artists[artist] = ''.join(artist_concert_info[1:])
    return ew_artists
            
def format_concerts(my_concert_artists):
    """Create the string for output to the web """      
    artists_string = ''
    print("hmmm")
    #print("EWartists",ew_artists)
    i=100
    for artist in my_concert_artists:
        m = re.search('(?:[^,]*,){0,4}[^,]*',ew_artists[artist])
        print(i)
        i+=1
        if m:
            concert_string = m.group(0)
            print(concert_string)
        else:
            concert_string = ew_artists[artist]
            print(concert_string)
        artists_string += artist + ': ' + concert_string + '<br>'
    print("almost home")
    return artists_string
       


def get_rdio_ewconcerts(username):
    """Find all EW-listed concerts by username's Rdio collection artists."""
    # Pick up the Rdio artists and all the EW concerts
    print("1")
    artists = get_rdio_artists(username)
    print("2")
    ew_artists = get_all_concerts()
    print("3")
    #print("First EW, ", ew_artists)
    # Just want concerts from Rdio artists     
    my_concert_artists = artists.intersection(ew_artists) 
    print("4")
    # String it up
    print(my_concert_artists)
    return format_concerts(my_concert_artists)

# Call the get_rdio_ewconcerts function based on the URL
app = Flask(__name__)
@app.route('/<username>')
def get_username(username):
    print("What is happening.")
    return get_rdio_ewconcerts(username)
@app.route('/')
def hello():
    return "Did you forget your username?"