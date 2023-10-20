import base64, json, random
import requests as rq, tweepy as tw, spotipy as sp
from details import credentials
from spotipy.oauth2 import SpotifyOAuth

sc = credentials['Spotify']
tc = credentials['Twitter']

bot = tw.Client(consumer_key=tc['API_Key'], consumer_secret=tc['API_Key_Secret'],
                access_token=tc['Access_Token'], access_token_secret=tc['Access_Token_Secret'])

def post_tweet(text):
    bot.create_tweet(text=text)


def spotify_token():
    auth_string = sc['CLIENT_ID'] + ':' + sc['CLIENT_SECRET']
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

    url = 'https://accounts.spotify.com/api/token'

    headers = {'Authorization': 'Basic ' + auth_base64, 
               'Content-Type': 'application/x-www-form-urlencoded'}
    
    data = {'grant_type': 'client_credentials',
            'scope': 'user-follow-read'}
    
    result = rq.post(url, headers=headers, data=data)

    json_result = json.loads(result.content)

    token = json_result['access_token']
    return token

artist_list = [] # list of artist objects, will store artists the user follows

class Artist():
    def __init__(self, name):
        self.name = name

        artist_result = rq.get(f'https://api.spotify.com/v1/search?q={self.name}&type=artist&limit={str(1)}', headers={'Authorization': 'Bearer ' + spotify_token()})
        self.artist_respose = json.loads(artist_result.content)

        self.artist_name = self.artist_respose['artists']['items'][0]['name']
        self.id = self.artist_respose['artists']['items'][0]['id']

        artist_top_tracks = rq.get(f'https://api.spotify.com/v1/artists/{self.id}/top-tracks?country={"GB"}', headers={'Authorization': 'Bearer ' + spotify_token()})
        self.top_tracks = json.loads(artist_top_tracks.content)['tracks']

        artist_albums = rq.get(f'https://api.spotify.com/v1/artists/{self.id}/albums', headers={'Authorization': 'Bearer ' + spotify_token()})
        artist_albums_result = json.loads(artist_albums.content)['items']
    
        self.albums = {}
        self.albums_links = {}
        for i in artist_albums_result:
            if i['album_group'] == 'appears_on':
                pass
            else:
                self.albums[i['name']]=i['id']
                self.albums_links[i['name']]=i['external_urls']['spotify']


    def album_type(self, album_id):
        album_type_ask = rq.get(f'https://api.spotify.com/v1/albums/{album_id}', headers={'Authorization': 'Bearer ' + spotify_token()})
        album_type_result = json.loads(album_type_ask.content)

        album_type = album_type_result['album_type']

        return album_type


    def album_tracklist(self, album_id):
        album_tracks = rq.get(f'https://api.spotify.com/v1/albums/{album_id}/tracks', headers={'Authorization': 'Bearer ' + spotify_token()})
        album_tracks_result = json.loads(album_tracks.content)

        tracklist = {}

        for i in album_tracks_result['items']:
            tracklist[i['name']]=i['external_urls']['spotify']

        return tracklist


spot = sp.Spotify(auth_manager=SpotifyOAuth(client_id=sc['CLIENT_ID'], client_secret=sc['CLIENT_SECRET'], redirect_uri='https://open.spotify.com/', scope='user-follow-read'))
for offset in range(0, 1000, 50):
    response = spot.current_user_followed_artists(limit=50, after=offset)
    for i in response['artists']['items']:
        artist_list.append(i['name'])


def random_album():
    album_type = 'single'
    while album_type == 'single':
        artist = Artist(random.choice(artist_list))
        album = random.choice(list(artist.albums.keys()))
        album_type = artist.album_type(artist.albums[album])

    return f"""
Album suggestion of the day:

'{album}' by {artist.artist_name}
{artist.albums_links[album]}
"""

post_tweet(random_album())
print("Tweet tweeted")