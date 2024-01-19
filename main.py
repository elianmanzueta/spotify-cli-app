"""Spotify CLI App"""
import os
import logging
import json
from typing_extensions import Annotated
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
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

    # Default values for time_range and limit.
    DEFAULT_TIME_RANGE = "medium_term"

    # The max result limit is 50.
    DEFAULT_RESULT_LIMIT = 20

    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.redirect_uri = os.getenv("REDIRECT_URI")

        # Use rich logger.
        self.log = logging.getLogger("rich")

    def credentials(self):
        """
        Regular authentication to use the API.

        Does not require user authentication
        """
        client_credentials_manager = SpotifyClientCredentials(
            client_id=self.client_id, client_secret=self.client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        return sp

    def session_constructor(self, scope: str) -> spotipy.Spotify:
        """
        Authenticates to use API.
        
        Used for user authentication.

        Args:
            scope (str): Permission scope of request.

        Raises:
            typer.Exit: Raised if there are Spotify API exceptions or authentication errors.

        Returns:
            spotipy.Spotify: Returns a usable API session.
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
            self.log.error("Exiting: OAuth Error:\n%s", e)
            raise typer.Exit(code=1)
        return session

    def current_user_display_name(self) -> str:
        """
        Get the current user's display name.
        """

        scope = "user-top-read"

        session = self.session_constructor(scope)
        user = session.current_user()
        self.log.debug(json.dumps(user, indent=4))
        return user["display_name"]

    def top_prompt(self, time_range: str, prompt_type: str):
        """
        Used to control what is shown in the first line of the top_tracks and top_artists functions.

        Args:
            time_range (str, optional): Time range of results. Defaults to None.
            prompt_type (str, optional): Type of prompt (artists, tracks). Defaults to None.
        """
        display_name = self.current_user_display_name()
        if time_range == "short_term":
            console.print(
                f"[i]Displaying [bold green]{display_name}'s[/bold green] top {prompt_type} in the last month!\n[/i]",
                justify="center",
            )
        elif time_range == "medium_term":
            console.print(
                f"[i]Displaying [bold green]{display_name}'s[/bold green] top {prompt_type} in the last six months!\n[/i]",
                justify="center",
            )
        elif time_range == "long_term":
            console.print(
                f"[i]Displaying [bold green]{display_name}'s[/bold green] top {prompt_type} of all time!\n[/i]",
                justify="center",
            )

    def get_track_duration(
        self, authentication: spotipy.Spotify, track_uri: str
    ) -> int:
        """
        Gets a given track's duration.

        Args:
            authentication (spotipy.Spotify): Authenticated API session.
            track_uri (str): The track's uri.

        Returns:
            int: Returns the duration of a track in milliseconds.
        """
        authentication = self.credentials()
        track_info = authentication.track(track_uri)
        return track_info["duration_ms"]

    def ms_to_minutes_and_seconds(self, ms: int) -> str:
        """
        Used to convert the track's duration (ms) to format seconds:minutes.

        Args:
            ms (int): Track length in milliseconds.

        Returns:
            str: Returns the track's duration in format seconds:minutes.
        """
        total_seconds = int(ms / 1000)

        # Calculate minutes and seconds
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes}:{str(seconds).zfill(2)}"

    def current_user_top_tracks(
        self, time_range: str = None, limit: int = None
    ) -> list:
        """
        Gets the user's top tracks.

        Args:
            time_range (str, optional): The time range of the results. Defaults to DEFAULT_TIME_RANGE.
            limit (int, optional): _description_. Defaults to DEFAULT_RESULT_LIMIT.

        Raises:
            typer.Exit: Raised if the Spotify API returns an exception..one.

        Returns:
            list: Returns a list of the user's top tracks.
        """
        # Use class defaults if no value is provided
        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_RESULT_LIMIT

        scope = "user-top-read"

        try:
            # Create a session to get the user's information and their top tracks.
            session = self.session_constructor(scope)
            top_tracks = session.current_user_top_tracks(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n%s", e)
            raise typer.Exit(code=1)

        self.log.debug(json.dumps(top_tracks, indent=4))

        # Iterate through "items" to extract the song name and artist name.
        tracklist = []
        for idx, track in enumerate(top_tracks["items"]):
            track_name = track.get("name")
            track_uri = track.get("uri")
            track_length_in_ms = self.get_track_duration(auth, track_uri)
            track_length = self.ms_to_minutes_and_seconds(track_length_in_ms)
            artist_names = track["artists"][0]["name"]
            tracklist.append(
                f"[bold green]{idx+1}[/bold green] - {track_name} by {artist_names} ({track_length})"
            )

        self.top_prompt(time_range, "songs")
        for track in tracklist:
            console.print(track, justify="center")

        return tracklist

    def current_user_top_artists(
        self, time_range: str = None, limit: int = None
    ) -> list:
        """
        Gets the user's top artists.

        Args:
            time_range (str, optional): The time range of the results. Defaults to DEFAULT_TIME_RANGE.
            limit (int, optional): _description_. Defaults to DEFAULT_RESULT_LIMIT.

        Raises:
            typer.Exit: Raised if the Spotify API returns an exception.

        Returns:
            list: Returns a lists of artists and their associated genres.
        """

        # Use class defaults if no value is provided
        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_RESULT_LIMIT

        scope = "user-top-read"

        try:
            # Create a session to get user information and top tracks.
            session = self.session_constructor(scope)
            top_artists = session.current_user_top_artists(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n%s", e)
            raise typer.Exit(code=1)

        self.log.debug(json.dumps(top_artists, indent=4))

        self.top_prompt(time_range, "artists")
        artistlist = []
        # Iterate through "items" to extract the artist name and their genres.
        for idx, artist in enumerate(top_artists["items"]):
            artist_name = artist.get("name", "Unknown Artist")
            artist_genres = artist.get("genres", "Unknown Genre")
            if artist_genres:
                genres = ", ".join(str(x) for x in artist_genres)
            else:
                genres = "No genres found"
            console.print(
                f"[bold green]{idx+1}[/bold green] - {artist_name} - {genres}",
                justify="center",
            )
            artistlist.append(
                f"[bold green]{idx+1}[/bold green] - {artist_name} - {genres}"
            )
        return artistlist

    def search_spotify(
        self,
        query: str,
        authentication: spotipy.Spotify,
        limit: int = 10,
        result_type: str = "tracks",
    ):
        """
        Searches Spotify.

        Args:
            query (str): The user query.
            authentication (spotipy.Spotify): Authenticated API session.
            limit (int): Amount of results to output. Defaults to 10
            result_type (str): The type of results that should be outputted. Defaults to 'tracks'.

        Returns:
            dict: Returns search results as a dictionary.
        """
        limit = limit if limit is not None else 10

        if result_type == "artist":
            result = authentication.search(query, type="artist", limit=limit)
        elif result_type == "track":
            result = authentication.search(query, type="track", limit=limit)
        self.log.debug(json.dumps(result, indent=4))
        return result


# Load environment variables from .env
load_dotenv()

# Rich
console = Console(highlight=False)

# Typer
app = typer.Typer()
state = {"verbose": False}

# Client initialization and authentication.
client = SpotifyClient()
auth = client.credentials()


# Logging
@app.callback()
def main(verbose: bool = False):
    """
    Sets the script's logging level. Default is INFO.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    else:
        logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])


# Typer commands
# Wrapper functions that call class methods.
@app.command()
def get_top_songs(
    time_range: Annotated[
        str,
        typer.Option(
            default="medium_term",
            help="Takes three options: short_term, medium_term, long_term",
        ),
    ] = "medium_term",
    limit: Annotated[
        int, typer.Option(default=20, help="The amount of results shown. Limit of 50")
    ] = 20,
):
    """
    Gets the current user's top songs.

    Args:
        time_range (str): Time range of results. Defaults to "medium_term".
        limit (int): The amount of results to show. Defaults to 20.

    Returns:
        list: Returns a list of the user's top tracks in a given time_range.
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
        int, typer.Option(default=20, help="The amount of songs shown. Limit of 50")
    ] = 20,
):
    """
    Get the users top artists.

    Args:
        time_range (str, optional): Time range of results. Defaults to "medium_term".
        limit (int, optional): The amount of results shown. Defaults to 20.

    Returns:
        list: Returns a list of the user's top artists in a given time_range.
    """
    return client.current_user_top_artists(time_range, limit)


@app.command()
def search(
    artist: Annotated[
        str, typer.Option(default=None, help="Artist to search for.")
    ] = None,
    track: Annotated[
        str, typer.Option(default=None, help="Track to search for.")
    ] = None,
    limit: Annotated[
        int, typer.Option(default=10, help="Amount of results to output.")
    ] = 10,
):
    """
    Searches Spotify for artists or tracks.

    Args:
        artist (str, optional): Artist to search for. Defaults to None.
        track (str, optional): Track to search for. Defaults to None.
        limit (int, optional): The amount of results shown. Defaults to 10, max 50.
    """

    if track:
        results = client.search_spotify(
            query=track, authentication=auth, result_type="track", limit=limit
        )
        console.print(f'Results for: "[i]{track}[/i]":\n', justify="center")
        for idx, result in enumerate(results["tracks"]["items"]):
            artist_name = result["album"]["artists"][0]["name"]
            track_name = result["name"]
            console.print(
                f"[bold green]{idx+1}[/bold green] - {track_name} by {artist_name}",
                justify="center",
            )
    elif artist:
        results = client.search_spotify(
            query=artist, authentication=auth, result_type="artist", limit=limit
        )
        console.print(f'Results for "[i]{artist}[/i]":\n', justify="center")
        for idx, result in enumerate(results["artists"]["items"]):
            artist_name = result["name"]
            genres = result["genres"]
            if genres != []:
                console.print(
                    f"[bold green]{idx+1}[/bold green] - {artist_name} - {", ".join(genres)}",
                    justify="center",
                )
            else:
                console.print(
                    f"[bold green]{idx+1}[/bold green] - {artist_name} - no genre(s) found",
                    justify="center",
                )


if __name__ == "__main__":
    app()
