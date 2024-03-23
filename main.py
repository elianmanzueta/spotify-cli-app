import logging
from typing_extensions import Annotated
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.logging import RichHandler
from src.spotify_cli import SpotifyClient

load_dotenv()

# Rich
console = Console(highlight=False)

# Typer
app = typer.Typer()
state = {"verbose": False}

client = SpotifyClient()

# Logging
@app.callback()
def main(verbose: bool = False):
    """
    Spotify CLI App: Interact with the Spotify Web API.

    This application allows users to access their Spotify data, including top tracks, top artists, and search functionality, directly from the command line.\n\n\n

    It leverages the Spotify Web API to fetch and display user-specific information based on the provided commands.\n\n\n

    Each command supports various options to customize the output, such as time range and result limits. Use --help with any command to see its specific options.\n\n\n

    Enable verbose mode to see detailed logging output.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    else:
        logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])


# Typer 
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
                    f"[bold green]{idx+1}[/bold green] - {artist_name} - {', '.join(genres)}",
                    justify="center",
                )

            console.print(
                f"[bold green]{idx+1}[/bold green] - {artist_name}",
                justify="center",
            )


if __name__ == "__main__":
    app()
