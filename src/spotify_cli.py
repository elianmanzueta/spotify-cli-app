"""Spotify CLI App"""
import os
import logging
import json
from typing_extensions import Annotated
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.logging import RichHandler


class SpotifyClient:
    """
    A wrapper class for interacting with the Spotify Web API using Spotipy.
    """

    # Default values for time ranges.
    VALID_TIME_RANGES = ["short_term", "medium_term", "long_term"]
    DEFAULT_TIME_RANGE = "medium_term"

    # Default value for result limits.
    DEFAULT_RESULT_LIMIT = 20
    MAX_RESULT_LIMIT = 50

    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        self._display_name = None
        self._user_scope = None
        self._user_session = None
        self._client_session = None

        # Use rich logger.
        self.log = logging.getLogger("rich")

    def authenticate(self, scope: str = None) -> spotipy.Spotify:
        """
        Create a Spotify client.

        Args:
            scope (str, optional): The scope of the user authorization process. Defaults to None.

        Returns:
            spotipy.Spotify: A Spotify client.
        """

        # User authentication
        if scope:
            if self._user_session is None or self._user_scope != scope:
                # Create a new session if one doesn't exist, or if the scope changes.
                self._user_session = spotipy.Spotify(
                    auth_manager=SpotifyOAuth(
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        redirect_uri=self.redirect_uri,
                        scope=scope,
                    )
                )
                self._user_scope = scope
            return self._user_session

        # Client credential authentication
        if self._client_session is None:
            # Create a new session if one doesn't exist.
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id, client_secret=self.client_secret
            )
            self._client_session = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager
            )
        return self._client_session

    @staticmethod
    def validate_time_range_and_limit(time_range: str = None, limit: int = None):
        """
        Validates the user's input for time_range and limit.

        Args:
            time_range (str): Time range of results. Defaults to None.
            limit (int): The amount of results shown. Defaults to None.

        Raises:
            ValueError: If time_range is not valid.
            ValueError: If limit is not valid.
        """

        if time_range is not None and time_range not in SpotifyClient.VALID_TIME_RANGES:
            raise ValueError(
                f"Invalid time range: {time_range}. Valid options: {', '.join(SpotifyClient.VALID_TIME_RANGES)}"
            )
        if limit is not None and (limit > SpotifyClient.MAX_RESULT_LIMIT or limit <= 0):
            raise ValueError(
                f"Invalid limit {limit}. Limit must be between 1 and {SpotifyClient.MAX_RESULT_LIMIT} "
            )

    def current_user_display_name(self) -> str:
        """
        Get the current user's display name.
        """

        scope = "user-top-read"

        if self._display_name is None:
            session = self.authenticate(scope)
            user = session.current_user()
            self._display_name = user["display_name"]
            return self._display_name

        return self._display_name

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

    def fetch_track_duration(
        self, authentication: spotipy.Spotify, track_uris: list
    ) -> list:
        """
        Gets a given track's duration.

        Args:
            authentication (spotipy.Spotify): Spotify API Client
            track_uri (list): A list of track URIs.

        Returns:
            list: Returns a list of track durations in milliseconds.
        """

        tracks = authentication.tracks(track_uris)
        track_duration_list = []

        for track in tracks["tracks"]:
            track_duration_list.append(track["duration_ms"])

        return track_duration_list

    @staticmethod
    def ms_to_minutes_and_seconds(track_durations: list):
        """
        Used to convert a given track's duration (ms) to format seconds:minutes.

        Args:
            track_durations (list): A list of track durations in milliseconds.

        Returns:
           list: Returns a list of formatted track durations.
        """

        track_durations_in_minutes = []

        for duration in track_durations:
            total_seconds = int(duration / 1000)

            minutes = total_seconds // 60
            seconds = total_seconds % 60

            track_durations_in_minutes.append(f"{minutes}:{str(seconds).zfill(2)}")

        return track_durations_in_minutes

    def current_user_top_tracks(
        self, time_range: str = None, limit: int = None
    ) -> list:
        """
        Gets the user's top tracks.

        Args:
            time_range (str, optional): The time range of the results. Defaults to DEFAULT_TIME_RANGE.
            limit (int, optional): The amount of results shown. Defaults to DEFAULT_RESULT_LIMIT.

        Raises:
            typer.Exit: Raised if the Spotify API returns an exception.

        Returns:
            list: Returns a list of the user's top tracks.
        """

        SpotifyClient.validate_time_range_and_limit(time_range, limit)

        # Use class defaults if no value is provided
        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_RESULT_LIMIT

        scope = "user-top-read"

        try:
            # Create a session to get the user's information and their top tracks.
            session = self.authenticate(scope)
            top_tracks = session.current_user_top_tracks(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n\n%s", e)
            raise typer.Exit(code=1)

        track_uri_list = []
        tracklist = []

        # Iterate through "items" to extract the song name and artist name.
        for idx, track in enumerate(top_tracks["items"]):
            track_name = track.get("name")
            track_uri = track.get("uri")
            track_uri_list.append(track_uri)
            artist_name = track["artists"][0]["name"]
            tracklist.append(
                f"[bold green]{idx+1}[/bold green] - {track_name} by {artist_name}"
            )

        track_durations_in_ms = self.fetch_track_duration(session, track_uri_list)
        track_duration_in_minutes = SpotifyClient.ms_to_minutes_and_seconds(
            track_durations_in_ms
        )

        # User output
        self.top_prompt(time_range, "tracks")
        for idx, track in enumerate(tracklist):
            console.print(
                f"{track} ({track_duration_in_minutes[idx]})", justify="center"
            )

        return tracklist

    def current_user_top_artists(
        self, time_range: str = None, limit: int = None
    ) -> list:
        """
        Gets the user's top artists.

        Args:
            time_range (str, optional): The time range of the results. Defaults to DEFAULT_TIME_RANGE.
            limit (int, optional): The amount of results shown. Defaults to DEFAULT_RESULT_LIMIT.

        Raises:
            typer.Exit: Raised if the Spotify API returns an exception.

        Returns:
            list: Returns a lists of artists and their associated genres.
        """

        SpotifyClient.validate_time_range_and_limit(time_range, limit)

        # Use class defaults if no value is provided
        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_RESULT_LIMIT

        scope = "user-top-read"

        try:
            # Create a session to get user information and top tracks.
            session = self.authenticate(scope)
            top_artists = session.current_user_top_artists(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n\n%s", e)
            raise typer.Exit(code=1)

        self.top_prompt(time_range, "artists")
        artistlist = []

        # Iterate through "items" to extract the artist name and their genres.
        for idx, artist in enumerate(top_artists["items"]):
            artist_name = artist.get("name", "Unknown Artist")
            artist_genres = artist.get("genres", "Unknown Genre")

            if artist_genres:
                genres = ", ".join(str(x) for x in artist_genres)

            else:
                # Handling if no genres are found for an artist.
                genres = "No genres found"

            artistlist.append(
                f"[bold green]{idx+1}[/bold green] - {artist_name} - {genres}"
            )

        for artist in artistlist:
            console.print(artist, justify="center")

        # Returns a list of found artists.
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
            authentication (spotipy.Spotify): A Spotify client.
            limit (int): The amount of results shown. Defaults to 10.
            result_type (str): The type of results that should be returned. Defaults to 'tracks'.

        Returns:
            dict: Returns search results as a dictionary.
        """

        SpotifyClient.validate_time_range_and_limit(limit=limit)

        limit = limit if limit is not None else 10

        if result_type == "artist":
            result = authentication.search(query, type="artist", limit=limit)
        elif result_type == "track":
            result = authentication.search(query, type="track", limit=limit)
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


# Logging
@app.callback()
def main(verbose: bool = False):
    """
    Spotify CLI App: Interact with the Spotify Web API.

    This application allows users to access their Spotify data, including top tracks, top artists, and search functionality, directly from the command line. It leverages the Spotify Web API to fetch and display user-specific information based on the provided commands.\n\n\n

    Each command supports various options to customize the output, such as time range and result limits. Use --help with any command to see its specific options.\n\n\n

    Enable verbose mode to see detailed logging output.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    else:
        logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])


# Typer commands.
# Wrapper functions that call class methods.
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
        int, typer.Option(default=20, help="The amount of results shown. Limit of 50")
    ] = 20,
):
    """
    Gets the current user's top tracks.

    Args:
        time_range (str): Time range of results. Defaults to "medium_term".
        limit (int): The amount of results shown. Defaults to DEFAULT_RESULT_LIMIT.

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
        int, typer.Option(default=20, help="The amount of results shown. Limit of 50")
    ] = 20,
):
    """
    Get the users top artists.

    Args:
        time_range (str, optional): Time range of results. Defaults to "medium_term".
        limit (int, optional): The amount of results shown. Defaults to DEFAULT_RESULT_LIMIT.

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
        limit (int, optional): The amount of results shown. Defaults to 10.
    """
    auth = client.authenticate()

    # If track option is set.
    if track:
        results = client.search_spotify(
            query=track, authentication=auth, result_type="track", limit=limit
        )
        console.print(
            f'Results for "[bold green][i]{track}[/i][/bold green]":\n',
            justify="center",
        )

        for idx, result in enumerate(results["tracks"]["items"]):
            try:
                artist_name = result["album"]["artists"][0]["name"]
                track_name = result["name"]
            except (KeyError, IndexError, TypeError):
                artist_name = None
                track_name = None

            console.print(
                f"[bold green]{idx+1}[/bold green] - {track_name} by {artist_name}",
                justify="center",
            )

    # If artist option is set.
    elif artist:
        results = client.search_spotify(
            query=artist, authentication=auth, result_type="artist", limit=limit
        )

        console.print(
            f'Results for "[bold green][i]{artist}[/i][/bold green]":\n',
            justify="center",
        )

        for idx, result in enumerate(results["artists"]["items"]):
            artist_name = result["name"]
            genres = result["genres"]

            # Checking if a given artist has any genres.
            if genres != []:
                console.print(
                    f"[bold green]{idx+1}[/bold green] - {artist_name} - {", ".join(genres)}",
                    justify="center",
                )

            console.print(
                f"[bold green]{idx+1}[/bold green] - {artist_name} - no genre(s) found",
                justify="center",
            )


if __name__ == "__main__":
    app()
