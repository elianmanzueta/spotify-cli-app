""""Spotify CLI App"""

import logging
import os
from typing import Optional

import spotipy
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from typing_extensions import Annotated


class SpotifyClient:
    """
    A wrapper class for interacting with the Spotify API using Spotipy.
    """

    # Default values for time ranges.
    VALID_TIME_RANGES = ["short_term", "medium_term", "long_term"]
    DEFAULT_TIME_RANGE = "medium_term"

    # Default value for result limits.
    DEFAULT_RESULT_LIMIT = 20
    MAX_RESULT_LIMIT = 50

    console = Console(highlight=False)

    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        self._display_name = None
        self._user_scope = None
        self._user_session = None
        self._client_session = None

        self.log = logging.getLogger("rich")

    def authenticate(self, scope: Optional[str] = None) -> spotipy.Spotify:
        """
        Create a Spotify client.

        Args:
            scope (Optional[str]): Specifies permissions the client is requesting from the user. Defaults to None.

        Returns:
            spotipy.Spotify: A Spotify client.
        """

        # User authentication
        # If a scope is provided, a session with the specified scope is created if it doesn't exist or if the scope has changed.
        # Otherwise, client credential authentication is used to create a session if it doesn't exist.
        if scope:
            if self._user_session is None or self._user_scope != scope:
                self._user_session = spotipy.Spotify(
                    auth_manager=SpotifyOAuth(
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        redirect_uri=self.redirect_uri,
                        scope=scope,
                    )
                )
                self._user_scope = scope  # Update the scope of the user session.
            return self._user_session

        # Client credential authentication
        if self._client_session is None:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id, client_secret=self.client_secret
            )
            self._client_session = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager
            )

        # Return the session.
        return self._client_session

    @staticmethod
    def validate_time_range_and_limit(
        time_range: Optional[str] = None, limit: Optional[int] = None
    ):
        """
        Validates the time range and limit parameters.

        Args:
            time_range (Optional[str]): The time range to validate.
            limit (Optional[int]): The limit to validate.

        Raises:
            ValueError: If the time range is not valid or if the limit is not valid.

        Returns:
            None
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
        Return the display name of the current user.

        If the display name is not cached, it is fetched from the Spotify API.

        Returns:
            str: The display name of the current user.
        """

        scope = "user-top-read"

        if self._display_name is None:
            session = self.authenticate(scope)
            user = session.current_user()
            if user is not None:
                self._display_name = user["display_name"]
                return self._display_name
            return "Unable to fetch display name."
        return self._display_name

    def top_prompt(self, time_range: str, prompt_type: str):
        """
        Used to control what is shown in the first line of the top_tracks and top_artists functions.

        Args:
            time_range (str): Time range of results. Defaults to None.
            prompt_type (str): Type of prompt (artists, tracks). Defaults to None.
        """

        display_name = self.current_user_display_name()

        if time_range == "short_term":
            self.console.print(
                f"[i]Displaying [bold green]{display_name}'s[/bold green] top {prompt_type} in the last month!\n[/i]",
                justify="center",
            )

        elif time_range == "medium_term":
            self.console.print(
                f"[i]Displaying [bold green]{display_name}'s[/bold green] top {prompt_type} in the last six months!\n[/i]",
                justify="center",
            )

        elif time_range == "long_term":
            self.console.print(
                f"[i]Displaying [bold green]{display_name}'s[/bold green] top {prompt_type} of all time!\n[/i]",
                justify="center",
            )

    def fetch_track_duration(
        self, authentication: spotipy.Spotify, track_uris: list[str]
    ) -> list[int]:
        """
        Fetches the duration of the given track URIs using the provided authentication.

        Args:
            authentication (spotipy.Spotify): An authenticated Spotify client.
            track_uris (list[str]): A list of track URIs for which to fetch the duration.

        Returns:
            list[int]: A list of integers representing the duration of each track in milliseconds.
        """
        tracks = authentication.tracks(track_uris)
        track_duration_list = []

        if tracks is not None:
            for track in tracks["tracks"]:
                track_duration_list.append(track["duration_ms"])
        return track_duration_list

    @staticmethod
    def ms_to_minutes_and_seconds(track_durations: list[int]) -> list[str]:
        """
        Convert milliseconds to minutes and seconds for each duration in the input list.

        Args:
            track_durations (list[int]): A list of integers representing durations in milliseconds.

        Returns:
            list: A list of strings in the format "minutes:seconds" for each duration.
        """

        track_durations_in_minutes = []

        for duration in track_durations:
            total_seconds = int(duration / 1000)

            minutes = total_seconds // 60
            seconds = total_seconds % 60

            track_durations_in_minutes.append(f"{minutes}:{str(seconds).zfill(2)}")

        return track_durations_in_minutes

    def current_user_top_tracks(
        self, time_range: Optional[str] = None, limit: Optional[int] = None
    ) -> list[str]:
        """
        Retrieves the top tracks for the current user based on their listening history.

        Args:
            time_range (Optional[str]): The time range to consider for the top tracks.
                Possible values are "short_term", "medium_term", and "long_term".
                Defaults to None, which means the default time range specified in the class will be used.
            limit (Optional[int]): The maximum number of top tracks to retrieve.
                Defaults to None, which means the default result limit specified in the class will be used.

        Returns:
            list[str]: A list of strings representing the top tracks. Each string contains the track name,
                artist name, and track duration in minutes and seconds.

        Raises:
            typer.Exit: If there is an error with the Spotify API or if no top tracks are found.
        """

        SpotifyClient.validate_time_range_and_limit(time_range, limit)

        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_RESULT_LIMIT

        scope = "user-top-read"

        try:
            session = self.authenticate(scope)
            top_tracks = session.current_user_top_tracks(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n\n%s", e)
            raise typer.Exit(code=1)

        if top_tracks is None:
            self.console.print("No top tracks found.")
            raise typer.Exit(code=1)

        track_uri_list = []
        tracklist = []

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

        self.top_prompt(time_range, "tracks")
        for idx, track in enumerate(tracklist):
            self.console.print(
                f"{track} ({track_duration_in_minutes[idx]})", justify="center"
            )

        return tracklist

    def current_user_top_artists(
        self, time_range: Optional[str] = None, limit: Optional[int] = None
    ) -> list[str]:
        """
        Generate a list of the current user's top artists based on the specified time range and limit.

        Args:
            time_range (Optional[str]): The time range to consider for the top tracks.
                Possible values are "short_term", "medium_term", and "long_term".
                Defaults to None, which means the default time range specified in the class will be used.
            limit (Optional[int]): The maximum number of top artists to retrieve.
                Defaults to None, which means the default result limit specified in the class will be used.

        Returns:
            list[str]: A list of strings containing the top artists' information formatted for display.
        """

        SpotifyClient.validate_time_range_and_limit(time_range, limit)

        time_range = time_range if time_range is not None else self.DEFAULT_TIME_RANGE
        limit = limit if limit is not None else self.DEFAULT_RESULT_LIMIT

        scope = "user-top-read"

        try:
            session = self.authenticate(scope)
            top_artists = session.current_user_top_artists(
                time_range=time_range, limit=limit
            )
        except SpotifyException as e:
            self.log.error("Exiting: Spotify API Error:\n\n%s", e)
            raise typer.Exit(code=1)

        if top_artists is None:
            self.console.print("No top artists found.")
            raise typer.Exit(code=1)

        self.top_prompt(time_range, "artists")
        artistlist = []

        for idx, artist in enumerate(top_artists["items"]):
            artist_name = artist.get("name", "Unknown Artist")
            artist_genres = artist.get("genres", "Unknown Genre")

            if artist_genres:
                genres = ", ".join(str(x) for x in artist_genres)

            else:
                genres = "No genres found"

            artistlist.append(
                f"[bold green]{idx+1}[/bold green] - {artist_name} - {genres}"
            )

        for artist in artistlist:
            self.console.print(artist, justify="center")

        return artistlist

    def search_spotify(
        self,
        query: str,
        authentication: spotipy.Spotify,
        limit: Optional[int] = 10,
        result_type: str = "tracks",
    ):
        """
        Search for tracks or artists on Spotify using the provided query.

        Args:
            query (str): The search query.
            authentication (spotipy.Spotify): An authenticated Spotify client.
            limit (Optional[int]): The maximum number of results to return. Defaults to 10.
            result_type (Optional[str]): The type of result to search for. Can be "artist" or "track". Defaults to "tracks".

        Returns:
            dict: The search results.

        Raises:
            ValueError: If the result_type is not "artist" or "track".
        """
        SpotifyClient.validate_time_range_and_limit(limit=limit)

        limit = limit if limit is not None else 10
        if result_type == "artist":
            result = authentication.search(query, type="artist", limit=limit)
            return result
        result = authentication.search(query, type="track", limit=limit)
        return result


# .env
load_dotenv()

# Rich
console = Console(highlight=False)

# Typer initialization
app = typer.Typer()
state = {"verbose": False}

# Client initialization and authentication
client = SpotifyClient()


# Root help message and logging configuration
@app.callback()
def main(verbose: bool = False):
    """
    Spotify CLI App: Interact with the Spotify Web API.

    This application allows users to access their Spotify data, including top tracks, top artists, and search functionality, directly from the command line.\n\n\n

    It leverages the Spotify Web API to fetch and display user-specific information based on the provided commands.\n\n\n

    Each command supports various options to customize the output, such as time range and result limits. Use --help with any command to see its specific options.\n\n\n
    
    Time ranges:\n\n\n

    short_term: 4 weeks\n\n
    medium_term: 6 months\n\n
    long_term: all time\n\n

    Enable verbose mode to see detailed Spotipy output.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    else:
        logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])


# Typer
@app.command()
def get_top_tracks(
    time_range: Annotated[
        Optional[str],
        typer.Option(
            default="medium_term",
            help="Takes three options: short_term, medium_term, long_term",
        ),
    ] = "medium_term",
    limit: Annotated[
        Optional[int],
        typer.Option(default=20, help="The amount of results shown. Has a limit of 50"),
    ] = 20,
):
    """
    Gets the current user's top tracks.

    Args:
        time_range (Optional[str]): Time range of results. Defaults to "medium_term".
        limit (Optional[int]): The amount of results shown. Defaults to 20.

    Returns:
        list: Returns a list of the user's top tracks in a given time_range.
    """
    return client.current_user_top_tracks(time_range, limit)


@app.command()
def get_top_artists(
    time_range: Annotated[
        Optional[str],
        typer.Option(
            default="medium_term",
            help="Takes three options: short_term, medium_term, and long_term",
        ),
    ] = "medium_term",
    limit: Annotated[
        Optional[int],
        typer.Option(default=20, help="The amount of results shown. Limit of 50"),
    ] = 20,
):
    """
    Get the users top artists.

    Args:
        time_range (Optional[str]): Time range of results. Defaults to "medium_term".
        limit (Optional[int]): The amount of results shown. Defaults to 20.

    Returns:
        list: Returns a list of the user's top artists in a given time_range.
    """
    return client.current_user_top_artists(time_range, limit)


@app.command()
def search(
    artist: Annotated[
        str, typer.Option(default=None, help="Artist to search for.")
    ] = "",
    track: Annotated[str, typer.Option(default=None, help="Track to search for.")] = "",
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
    if track and track.split():
        results = client.search_spotify(
            query=track, authentication=auth, result_type="track", limit=limit
        )
        console.print(
            f'Results for "[bold green][i]{track}[/i][/bold green]":\n',
            justify="center",
        )

        if results is not None:
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

    elif artist and artist.split():
        results = client.search_spotify(
            query=artist, authentication=auth, result_type="artist", limit=limit
        )

        console.print(
            f'Results for "[bold green][i]{artist}[/i][/bold green]":\n',
            justify="center",
        )
        if results is not None:
            for idx, result in enumerate(results["artists"]["items"]):
                artist_name = result["name"]
                genres = result["genres"]

                # Checking if a given artist has any genres.
                if genres != []:
                    console.print(
                        f"[bold green]{idx+1}[/bold green] - {artist_name} - {', '.join(genres)}",
                        justify="center",
                    )

                console.print(
                    f"[bold green]{idx+1}[/bold green] - {artist_name} - no genre(s) found",
                    justify="center",
                )
    else:
        print("Please provide an artist or track.")


if __name__ == "__main__":
    app()
