from flask import Flask, redirect, request, render_template, session, url_for
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
from collections import Counter

app = Flask(__name__)  # Initialize Flask application
app.secret_key = os.urandom(24)  # Set a secret key for the application

# Spotify API credentials
SPOTIFY_CLIENT_ID = 'Add your client ID here'
SPOTIFY_CLIENT_SECRET = 'Add your client secret here'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = 'user-library-read user-read-recently-played user-top-read'

@app.route('/')
def index():
    return render_template('index.html')  # Render the index.html template

@app.route('/login')
def login():
    # Redirect users to Spotify login page
    sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET,
                            redirect_uri=SPOTIFY_REDIRECT_URI, scope=SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)  # Redirect to Spotify authorization URL

@app.route('/callback')
def callback():
    code = request.args.get('code')
    sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET,
                            redirect_uri=SPOTIFY_REDIRECT_URI, scope=SCOPE)
    token_info = sp_oauth.get_access_token(code)  # Get access token using authorization code
    if token_info:
        session['token_info'] = token_info  # Store token info in session
        target_url = session.pop('target_url', None)
        if target_url:
            return redirect(target_url)  # Redirect to target URL after successful login
        else:
            return redirect('/')  # Redirect to home page
    else:
        return "Failed to obtain access token."  # Display error message if access token retrieval fails

@app.route('/top-tracks')
def top_tracks():
    token_info = session.get('token_info')
    if not token_info:
        return redirect('/login')  # Redirect to login if token info is not found in session

    time_range = request.args.get('time_range', 'short_term')  # Get selected time range from request URL
    sp = spotipy.Spotify(auth=token_info['access_token'])
    top_tracks = sp.current_user_top_tracks(limit=50, offset=0, time_range=time_range)  # Get user's top tracks
    tracks = []
    for track in top_tracks['items']:
        album_images = track['album']['images']
        image_url = album_images[0]['url'] if album_images else None
        tracks.append({'name': track['name'], 'image_url': image_url})
    return render_template('top_tracks.html', tracks=tracks)  # Render top_tracks.html template with track data

@app.route('/top-artists')
def top_artists():
    token_info = session.get('token_info')
    if not token_info:
        return redirect('/login')  # Redirect to login if token info is not found in session

    time_range = request.args.get('time_range', 'short_term')  # Get selected time range from request URL
    sp = spotipy.Spotify(auth=token_info['access_token'])
    top_artists = sp.current_user_top_artists(limit=50, offset=0, time_range=time_range)  # Get user's top artists
    artists = []
    for artist in top_artists['items']:
        image_url = artist['images'][0]['url'] if artist['images'] else None
        artists.append({'name': artist['name'], 'image_url': image_url})
    return render_template('top_artists.html', artists=artists)  # Render top_artists.html template with artist data

@app.route('/top-genres')
def top_genres():
    token_info = session.get('token_info')
    if not token_info:
        return redirect('/login')  # Redirect to login if token info is not found in session

    time_range = request.args.get('time_range', 'short_term')  # Get selected time range from request URL
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # Retrieve the user's top tracks
    top_tracks = sp.current_user_top_tracks(limit=50, offset=0, time_range=time_range)

    # Extract genres from the top tracks' artists
    genres = []
    for track in top_tracks['items']:
        artists = track['artists']
        for artist in artists:
            # Extract artist ID
            artist_id = artist['id']
            # Retrieve artist info
            artist_info = sp.artist(artist_id)
            # Check if 'genres' key is present in artist_info
            if 'genres' in artist_info:
                genres.extend(artist_info['genres'])

    # Count the occurrence of each genre
    genre_counts = Counter(genres)

    # Sort genres by frequency
    top_genres = [genre for genre, count in genre_counts.most_common()]

    return render_template('top_genres.html', top_genres=top_genres)



@app.route('/logout')
def logout():
    # Logout logic
    session.pop('logged_in', None)
    return redirect(url_for('index'))  # Redirect to home page after logout

if __name__ == '__main__':
    app.run(debug=True)
