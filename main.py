"""os module provides lets us grab env variables."""
import os
import json
import logging
from typing_extensions import Annotated
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOauthError
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.logging import RichHandler


class SpotifyClient:
    """
    A wrapper class for interacting with the Spotify Web API using Spotipy.
    """

    # Default values for time_range and limit
    DEFAULT_TIME_RANGE = "medium_term"
    DEFAULT_LIMIT = 20

    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.redirect_uri = os.getenv("REDIRECT_URI")

        # Use rich logger
        self.log = logging.getLogger("rich")

        # Test for .env
        if not any([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError(
                "Missing required environment variables for the Spotify API."
            )

    def session_constructor(self, scope: str) -> spotipy.Spotify:
        """
        Constructs a Spotify API session.

        Reads environment variables for user credentials and the redirect URI.

        :param scope: Scope of information shared. Used for authorization purposes in the Spotify API.
        """

        try:
            session = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope=scope,
                )
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n%s", e)
            raise typer.Exit(code=1)
        except SpotifyOauthError as e:
            self.log.error ("Exiting: OAuth Error:\n%s", e)
            raise typer.Exit(code=1)
        return session

    def current_user_information(self) -> dict:
        """
        Get the current user's user information.
        """

        scope = "user-top-read"

        session = self.session_constructor(scope)
        user = session.current_user()
        self.log.info(user)
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
            # Create session to get user information and top tracks.
            session = self.session_constructor(scope)
            user_info = self.current_user_information()
            display_name = user_info["display_name"]
            top_tracks = session.current_user_top_tracks(
                time_range=time_range, limit=limit
            )
            print(json.dumps(top_tracks, indent=4))
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n%s", e)
            raise typer.Exit(code=1)
        tracklist = []
        for idx, track in enumerate(top_tracks["items"]):
            song_name = track.get("name")
            artists = track.get("artists")
            artist = artists[0] if artists else {}
            artist_name = artist.get("name", "Unknown Artist")
            tracklist.append(
                f"[bold green]{idx+1}[/bold green] - {song_name} by {artist_name}"
            )

        console.print(
            f"[i][bold green]{display_name}'s[/bold green] top [bold green]{time_range}[/bold green] songs :musical_notes:\n",
            highlight=False,
        )
        for track in tracklist:
            console.print(track, highlight=False)
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
            # Create a session to get user information and top tracks.
            session = self.session_constructor(scope)
            user_info = self.current_user_information()
            display_name = user_info["display_name"]
            top_artists = session.current_user_top_artists(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n%s", e)
            raise typer.Exit(code=1)
        console.print(
            f"[i][bold green]{display_name}'s[/bold green] top [bold green]{time_range}[/bold green] artists[/i] :musical_notes:\n",
            highlight=False,
        )
        artistlist = []
        for idx, artist in enumerate(top_artists["items"]):
            artist_name = artist.get("name", "Unknown Artist")
            artist_genres = artist.get("genres", "Unknown Genre")
            if artist_genres:
                genres = ", ".join(str(x) for x in artist_genres)
            else:
                genres = "No genres found"
            console.print(
                f"[bold green]{idx+1}[/bold green] - {artist_name} - {genres}",
                highlight=False,
            )
            artistlist.append(
                f"[bold green]{idx+1}[/bold green] - {artist_name} - {genres}"
            )
        return artistlist


# .env
load_dotenv()

# Rich
console = Console()

# Typer
app = typer.Typer()
state = {"verbose": False}

# Client object initialization
client = SpotifyClient()


# Logging
@app.callback()
def main(verbose: bool = False):
    """
    Set logging level. Default INFO.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    else:
        logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])


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
