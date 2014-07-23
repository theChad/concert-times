"""
Essential functions for getting upcoming concerts by Rdio artists.

"""

import os, re
from operator import itemgetter
from datetime import date
from datetime import datetime
from rauth import OAuth1Service
import urllib.parse, requests


def get_lastfm_concerts(city):
    api_key=os.environ['LASTFM_KEY']
    # Parameters to pass to the Last.fm API. We'll be calling the geo.getevents method and
    # using a limit of 1000 to try to ensure all the concerts show up. By default it gets
    # 'nearby' concerts, but I can change that later to specify the exact distance.
    params=urllib.parse.urlencode({'location': city, 'api_key': api_key, 
                                   'format': 'json','method': 'geo.getevents',
                                   'limit':1000})
    getevents_request=requests.get("http://ws.audioscrobbler.com/2.0/",params=params)
    events = getevents_request.json()['events']['event'] #map of concerts
    concerts_info={}
    for event in events:
        artists = event['artists']['artist'] #This can be a list of artists.
        if isinstance(artists,list):
            for artist in artists:
                print(artist)
                if not artist in concerts_info:
                    concerts_info[artist]=[]
                # Date is listed as date then time
                event_date=event['startDate'][:-9] #slice the date
                event_time=event['startDate'][-8:-3] #slice the time, minus seconds.
                concert_info={'artist': artist, 'venue': event['venue']['name'],
                              'date': event_date, 'time': event_time}
                concerts_info[artist].append(concert_info)
        else:
            artist = artists # this is a solo act
            print('solo:, ',artist)
            if not artist in concerts_info:
                concerts_info[artist]=[]
            # Date is listed as date then time
            event_date=event['startDate'][:-9] #slice the date
            event_time=event['startDate'][-8:-3] #slice the time, minus seconds.
            concert_info={'artist': artist, 'venue': event['venue']['name'],
                          'date': event_date, 'time': event_time}
            concerts_info[artist].append(concert_info)  
    return concerts_info
                
        

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
    """Return a dictionary of all concerts on the Early Warnings page, indexed by artist.
    Each artist's entry is a list of their upcoming shows in text (most of length 1)."""
    #Parse Early Warning concerts
    chicagoReader = requests.get('http://www.chicagoreader.com/chicago/EarlyWarnings')
    reader_html = chicagoReader.text
    # Each concert element starts with the same html list element
    ew_artists_spots = [m.start() for m in re.finditer('<li class="l0 event', reader_html)]
    # Find the last event's end
    m_last=re.search('</li>',reader_html[ew_artists_spots[-1]:])
    ew_artists_spots.append(m_last.start()+ew_artists_spots[-1])
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
                        '(?P<time>[^,.]+)')
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

def last_concerts_by_date(concerts_info):   
    """Sadly, Last.fm dates are in a different format than EW. Probably better."""
    concert_list = [concert for artist in concerts_info for concert in concerts_info[artist]]
    for concert in concert_list:
        concert['pydate'] = datetime.strptime(concert['date'],'%a, %d %b %Y')
    concert_list_sorted=sorted(concert_list,key=itemgetter('pydate'))
    print(concert_list_sorted)
    return concert_list_sorted

            
def format_concerts(my_concerts):
    """Create the string for output to the web """      
    concerts_string = '<!DOCTYPE HTML><html><head><style> body {background-color:#c6e4ff} ' +\
    '</style></head><body>'
    index_month=date.today().month-1
    for concert in my_concerts:
        if concert['pydate'].month > index_month:
            index_month = concert['pydate'].month
            concerts_string += '<h2>' + concert['pydate'].strftime("%B") + '</h2>'
        concerts_string += '<strong>' + concert['artist'] + '</strong>' + '&nbsp&nbsp' + \
        concert['venue'] + ', ' + concert['time'] + ', ' + concert['date'] + '<br>'
    concerts_string+='</body></html>'
    return concerts_string
       


def get_rdio_ewconcerts(username):
    """Find all EW-listed concerts by username's Rdio collection artists."""
    # Pick up the Rdio artists and all the EW concerts
    artists = get_rdio_artists(username)
    ew_artists = get_all_concerts()
    # Just want concerts from Rdio artists   
    my_concert_artists = artists.intersection(ew_artists) 
    my_concerts={artist:ew_artists[artist] for artist in my_concert_artists}
    # Reorganize my_concerts so I can pick out the dates
    my_concerts_dict = org_concert_info(my_concerts)
    my_concerts_list = concerts_by_date(my_concerts_dict)
    # String it up
    return format_concerts(my_concerts_list)

def get_rdio_lastfm_concerts(username,city):
    """Find all last.fm-listed concerts by username's Rdio collection artists."""
    # Pick up the Rdio artists and all the EW concerts
    artists = get_rdio_artists(username)
    last_artists = get_lastfm_concerts(city)
    # Just want concerts from Rdio artists   
    my_concert_artists = artists.intersection(last_artists) 
    my_concerts={artist:last_artists[artist] for artist in my_concert_artists}
    #my_concerts = last_artists
    # Reorganize my_concerts so I can pick out the dates
    my_concerts_list = last_concerts_by_date(my_concerts)
    # String it up
    return format_concerts(my_concerts_list)
    

