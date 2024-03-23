"""Spotify CLI App"""

import logging
import os
import spotipy
import typer
from rich.console import Console
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from typing import Optional


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

    console = Console(highlight=False)

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

    def authenticate(self, scope: Optional[str] = None) -> spotipy.Spotify:
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
    def validate_time_range_and_limit(
        time_range: Optional[str] = None, limit: Optional[int] = None
    ):
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
            if user is not None:
                self._display_name = user["display_name"]
                return self._display_name
            else:
                return "unable to get spotify user"
        else:
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

        if tracks is not None:
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
        self, time_range: Optional[str] = None, limit: Optional[int] = None
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
            return result
        elif result_type == "track":
            result = authentication.search(query, type="track", limit=limit)
            return result
        else:
            self.console.print("No search results found.")
            raise typer.Exit(code=1)
