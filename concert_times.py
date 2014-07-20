"""
Essential functions for getting upcoming concerts by Rdio artists.

"""

import os, re
from operator import itemgetter
from datetime import date
from rauth import OAuth1Service
import urllib.parse, requests

def get_rdio_artists(username):
    """Get all the artists in username's Rdio collection"""
    print('Do i at least get here?')
    # Create Rdio OAuth object 
    rdio = OAuth1Service(
        name='Rdio',
        consumer_key=os.environ['RDIO_KEY'],
        consumer_secret=os.environ['RDIO_SECRET'],
        request_token_url='http://api.rdio.com/oauth/request_token',
        access_token_url='http://api.rdio.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authorize',
        base_url='http://api.rdio.com/1/')
    print('I didn\'t change this.')
    #Open a signed, unathorized Rdio session
    session = rdio.get_session()
    #Get the Rdio user key
    params = urllib.parse.urlencode({'method': 'findUser', 'vanityName': username})
    findUser_result = session.post('',data = params)
    userKey = findUser_result.json()['result']['key']
    #Collect all Rdio artists
    print('or this.')
    params = urllib.parse.urlencode({'method': 'getArtistsInCollection', 'user': userKey})
    artists_result = session.post('', data = params)
    if artists_result.json()['status'] == 'ok':
        artists = {x['name'] for x in artists_result.json()['result']}
    return artists

def get_all_concerts():
    """Return a dictionary of all concerts on the Early Warnings page, indexed by artist.
    Each artist's entry is a list of their upcoming shows (most of length 1)."""
    #Parse Early Warning concerts
    chicagoReader = requests.get('http://www.chicagoreader.com/chicago/EarlyWarnings')
    reader_html = chicagoReader.text
    # Each concert element starts with the same html list element
    ew_artists_spots = [m.start() for m in re.finditer('<li class="l0 event">', reader_html)]
    # Assume the last event will be about as much space as the first
    ew_artists_spots.append(ew_artists_spots[1]-ew_artists_spots[0]+\
                            ew_artists_spots[len(ew_artists_spots)-1])
    ew_artists = {}
    # loop through each concert. Is this the fastest way to do this?
    for i in range(len(ew_artists_spots)-1):
        raw_data = reader_html[ew_artists_spots[i]:ew_artists_spots[i+1]]
        artist_concert_info = [x for x in re.split('<[^>]+>\s*',raw_data) if not x=='']
        current_artists = artist_concert_info[0].split(', ')
        for artist in current_artists:
            # Some artists have multiple upcoming shows
            if not artist in ew_artists:  
                ew_artists[artist] = [''.join(artist_concert_info[1:])]
            else:
                ew_artists[artist].append(''.join(artist_concert_info[1:]))
    return ew_artists

def org_concert_info(my_concerts):
    """Organize the dictionary of concert strings by artist into a dictionary of
    dictionaries, so I can more easily split out the date and organize by time"""
    concerts_info={}
    # Create the regex pattern for the concert info
    info_regex=re.compile('(?P<venue>[^,]*).*?(?P<date>[0-9]{1,2}/[0-9]{1,2}(-[0-9]{1,2})?),'
                        '(?P<time>[^,]+)')
    for artist, info_strings in my_concerts.items():
        concerts_info[artist]=[] # Some artists may have multiple upcoming shows
        for info_string in info_strings:
            m=info_regex.search(info_string)
            if m:
                concert_dict={'artist': artist}
                concert_dict.update(m.groupdict())
                concerts_info[artist].append(concert_dict)
    return concerts_info

def concerts_by_date(concerts_info):
    """Expects an organized dictionary of concerts. Currently wants it indexed by artist,
    each artist having a list of concert dictionaries (time, date, venue). Returns a list of 
    those dictionaries, sorted by date."""
    this_month = date.today().month
    this_year = date.today().year
    # Create a flat list of the individual concert info dictionaries
    concert_list = [concert for artist in concerts_info for concert in concerts_info[artist]]
    date_regex=re.compile('(?P<month>[^/]{1,2})/(?P<date>[0-9]{1,2})')
    for concert in concert_list:
        m = date_regex.search(concert['date'])
        month = int(m.group('month'))
        day = int(m.group('date'))
        year = this_year if month >= this_month else this_year+1
        concert['pydate'] = date(year,month,day)
    concert_list_sorted=sorted(concert_list,key=itemgetter('pydate'))
    return concert_list_sorted
    


            
def format_concerts(my_concerts):
    """Create the string for output to the web """      
    concerts_string = ''
    for concert in my_concerts:
        concerts_string += concert['artist'] + '<br>' + '&nbsp&nbsp&nbsp&nbsp&nbsp' + \
        concert['venue'] + 'at ' + concert['time'] + ', ' + concert['date'] + '<br>'
    
    return concerts_string
       


def get_rdio_ewconcerts(username):
    """Find all EW-listed concerts by username's Rdio collection artists."""
    # Pick up the Rdio artists and all the EW concerts
    print('1')
    artists = get_rdio_artists()
    print('1a')
    ew_artists = get_all_concerts()
    # Just want concerts from Rdio artists    
    print('2') 
    my_concert_artists = artists.intersection(ew_artists) 
    my_concerts={artist:ew_artists[artist] for artist in my_concert_artists}
    # Reorganize my_concerts so I can pick out the dates
    print('4')
    my_concerts_dict = org_concert_info(my_concerts)
    my_concerts_list = concerts_by_date(my_concerts_dict)
    # String it up
    print('5')
    return format_concerts(my_concerts_list)

