import os
from flask import Flask
from rauth import OAuth1Service
import urllib.parse, requests
import re

def get_rdio_ewconcerts(username):
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
    
    #Parse Early Warning concerts
    chicagoReader = requests.get('http://www.chicagoreader.com/chicago/EarlyWarnings')
    reader_html = chicagoReader.text
    ew_artists_spots = [m.start() for m in re.finditer('<li class="l0 event">', reader_html)]
    ew_artists_spots.append(len(reader_html))
    ew_artists = {}
    
    for i in range(len(ew_artists_spots)-1):
        raw_data = reader_html[ew_artists_spots[i]:ew_artists_spots[i+1]]
        artist_concert_info = [x for x in re.split('<[^>]+>\s*',raw_data) if not x=='']
        current_artists = artist_concert_info[0].split(',')
        for artist in current_artists:
            ew_artists[artist] = ''.join(artist_concert_info[1:])
            
         
    my_concert_artists = artists.intersection(ew_artists) 
    #Create the string for output to the web       
    artists_string = ''
    for artist in my_concert_artists:
        m = re.search('(?:[^,]*,){0,4}[^,]*',ew_artists[artist])
        if m:
            concert_string = m.group(0)
        else:
            concert_string = ew_artists[artist]
        artists_string += artist + ': ' + concert_string + '<br>'
    return artists_string
    

# Call the get_rdio_ewconcerts function based on the URL
app = Flask(__name__)
@app.route('/<username>')
def get_username(username):
    return get_rdio_ewconcerts(username)
@app.route('/')
def hello():
    return "Did you forget your username?"