"""
test some concert functions
"""
from concert_times import *
from datetime import date

if __name__ == '__main__':
    ew_artists = get_all_concerts()
    # Just want concerts from Rdio artists     
    #my_concert_artists = artists.intersection(ew_artists) 
    #my_concerts={artist:ew_artists[artist] for artist in my_concert_artists}
    # Reorganize my_concerts so I can pick out the dates
    my_concerts_dict = org_concert_info(ew_artists)
    #for artist,concert in my_concerts_dict.items():
    #    print(artist, concert)
    #print("Dessa?",my_concerts_dict['Dessa'])
    # String it up
    #return format_concerts(my_concerts)
    my_concerts_list=concerts_by_date(my_concerts_dict)
    for concerts in my_concerts_list:
        print(concerts['artist'],concerts['venue'],concerts['date'])
    print(format_concerts(my_concerts_list))

