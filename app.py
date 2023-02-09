from pymongo import MongoClient
import certifi

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from datetime import datetime

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

ca = certifi.where()

client = MongoClient(
    'mongodb+srv://spartsyl:U6V10Jk7juI7SMEX@Cluster0.fsdg43e.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.Bibimbap

cid = 'aa4b6b300fdb4797bfe7625e121c99cd'
secret = 'ddbca51759f340e58471ec1b929bad7b'
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/search_results", methods=["POST"])
def search_results():
    track_input_receive = request.form['track_input']
    track_search = sp.search(q=track_input_receive, limit=20, type='track', market=None)

    tracks = []
    track_ids = set()

    for track in track_search['tracks']['items']:
        track_results = track['name']
        trackid_results = track['id']
        artist_results = [artist['name'] for artist in track['artists']]
        image_results = next(
            (image['url'] for image in track['album']['images'] if image['height'] == 640 and image['width'] == 640),
            None)
        url_results = track['preview_url']

        datetime_input = datetime.now()
        date_input = datetime.now().date()
        hour_input = str(datetime.now().time())[:2]
        timestamp_input = (datetime_input.timestamp())

        track_result = {
            'track': track_results,
            'artists': artist_results,
            'image': image_results,
            'url': url_results,
            'date': date_input.strftime('%Y-%m-%d'),
            'hour': int(hour_input),
            'timestamp': int(timestamp_input),
            'trackID': trackid_results}

        if trackid_results not in track_ids:
            tracks.append(track_result)
            track_ids.add(trackid_results)
            db.search_results.insert_one(track_result)

    return 'OK'


@app.route("/search_results", methods=["GET"])
def playlist_get():
    playlist = list(db.search_results.find({}, {'_id': False}).sort([('timestamp', -1)]).limit(10))
    return jsonify({'track': playlist})


@app.route("/playlist", methods=["POST"])
def selected_track_post():
    selected_track_receive = request.form['select_track']
    selected_artists_receive = request.form['select_artists']
    existing_track = db.playlist.find_one({"track": selected_track_receive, "artists": selected_artists_receive})

    if existing_track is None:
        selected_track_data = db.search_results.find(
            {"track": selected_track_receive, "artists": selected_artists_receive})
        track_count = 1
        for track_data in selected_track_data:
            selected_track = {
                'track': track_data['track'],
                'artists': track_data['artists'],
                'image': track_data['image'],
                'url': track_data['url'],
                'hour': track_data['hour'],
                'count': track_count,
                'timestamp': track_data['timestamp'],
                'trackID': track_data['trackID']
            }
            db.playlist.insert_one(selected_track)

    else:
        db.playlist.update_one({"track": selected_track_receive, "artists": selected_artists_receive},
                               {"$inc": {"count": 1}})

    return 'OK'


@app.route("/playlist", methods=["GET"])
def selected_track_get():
    selected_track_id = list(db.playlist.find({}, {'_id': False}).sort([('timestamp', -1)]).distinct('trackID'))
    unique_tracks = []
    for track_id in selected_track_id:
        track_data = db.playlist.find_one({'trackID': track_id}, {'_id': False})
        unique_tracks.append(track_data)

    return jsonify({'selected_track': unique_tracks})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
