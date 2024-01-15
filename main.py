"""os module provides lets us grab env variables."""
import os
import logging
from typing_extensions import Annotated
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv
import typer
from rich import print


class SpotifyClient:
    """
    A wrapper class for interacting with the Spotify Web API using Spotipy.
    """

    DEFAULT_TIME_RANGE = "medium_term"
    DEFAULT_LIMIT = 20

    def __init__(self):
        self.display_name = None

    def session_constructor(self, scope: str) -> spotipy.Spotify:
        """
        Start a Spotify session.

        Reads environment variables for user credentials and redirect URI.

        :param scope: Scope of information shared
        """

        client_id = os.getenv("CLIENT_ID", None)
        client_secret = os.getenv("CLIENT_SECRET", None)
        redirect_uri = os.getenv("REDIRECT_URI", None)

        try:
            session = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    scope=scope,
                )
            )
        except SpotifyException as e:
            logging.error("Spotify API Error: %s", e)
            raise typer.Exit(code=1)
        return session

    def current_user_information(self) -> dict:
        """
        Get the current user's user information.

        {
        'display_name': 'Eliandawg',
        'external_urls': {'spotify': 'https://open.spotify.com/user/turmoilted'},
        'href': 'https://api.spotify.com/v1/users/turmoilted',
        'id': 'turmoilted',
        'images': [
            {'url': 'https://i.scdn.co/image/ab67757000003b823f51b6f12bb824b6d821a970', 'height': 64, 'width': 64},
            {'url': 'https://i.scdn.co/image/ab6775700000ee853f51b6f12bb824b6d821a970', 'height': 300, 'width': 300}
        ],
        'type': 'user',
        'uri': 'spotify:user:turmoilted',
        'followers': {'href': None, 'total': 22}
        }
        """
        scope = "user-top-read"

        try:
            session = self.session_constructor(scope)
            user = session.current_user()
        except SpotifyException as e:
            logging.error("Spotify API Error %s", e)
            raise typer.Exit(code=1)
        else:
            logging.info(user)
            return user

    def current_user_top_tracks(
        self, time_range: str = None, limit: int = None
    ) -> list:
        """
        Get the current user's top tracks.

        :param time_range: The time range to consider for top tracks.
        :param limit: The number of tracks to return.
        :return: List of top tracks.
        """

        # Use class defaults if no value is provided
        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_LIMIT

        scope = "user-top-read"

        try:
            # Create session and get user information and top tracks.
            session = self.session_constructor(scope)
            user_info = self.current_user_information()
            display_name = user_info["display_name"]
            top_tracks = session.current_user_top_tracks(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            logging.error("Spotify API Error: %s", e)
            raise typer.Exit(code=1)
        else:
            tracklist = []
            for track in top_tracks["items"]:
                song_name = track["name"]
                artist_name = track["artists"][0]["name"]
                tracklist.append(f"{song_name} - {artist_name}")

            print(f"[green]{display_name}'s top songs:")
            for track in tracklist:
                print(track)
            return tracklist

    def current_user_top_artists(
        self, time_range: str = None, limit: int = None
    ) -> list:
        """
        Get the current user's top artists.

        :param time_range: The time range to consider for top artists.
        :param limit: The number of artists to return.
        :return: List of top artists.
        """

        # Use class defaults if no value is provided
        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_LIMIT

        scope = "user-top-read"

        try:
            session = self.session_constructor(scope)
            top_artists = session.current_user_top_artists(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            logging.error("Spotify API Error: %s", e)
            raise typer.Exit(code=1)
        else:
            for artist in top_artists["items"]:
                artist_name = artist["name"]
                artist_genres = artist["genres"]
                print(f"{artist_name} - {", ".join(str(x) for x in artist_genres)}")


# Initialization
load_dotenv()
# logging.basicConfig(level=logging.DEBUG)
app = typer.Typer()
client = SpotifyClient()


# Typer commands
@app.command()
def get_user():
    """
    Get information on the current user.
    """
    return client.current_user_information()


@app.command()
def get_top_tracks(
    time_range: Annotated[
        str,
        typer.Option(
            default="medium_term",
            help="Takes three options: short_term, medium_term, long_term",
        ),
    ] = "medium_term",
    limit: Annotated[
        int, typer.Option(default=20, help="The amount of songs shown. Limit 50")
    ] = 20,
):
    """
    Get the current user's top tracks.

    Takes arguments time_range (default "medium_term") and limit (default 20).

    Term accepts three inputs
        short_term (past month)
        medium_term (six months)
        long_term (all time)
    """
    return client.current_user_top_tracks(time_range, limit)


@app.command()
def get_top_artists(
    time_range: Annotated[
        str,
        typer.Option(
            default="medium_term",
            help="Takes three options: short_term, medium_term, and long_term",
        ),
    ] = "medium_term",
    limit: Annotated[
        int, typer.Option(default=20, help="The amount of songs shown. Limit 50")
    ] = 20,
):
    """
    Get the current user's top artists.

    Takes arguments time_range (default "medium_term") and limit (default 20).

    Term accepts three inputs
        short_term (past month)
        medium_term (six months)
        long_term (all time)
    """
    return client.current_user_top_artists(time_range, limit)


if __name__ == "__main__":
    app()
