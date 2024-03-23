import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
import re
from typing import Any, Callable, Generator, Literal
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from main import app
from src.spotify_cli import SpotifyClient

logging.basicConfig(level=logging.DEBUG)

runner = CliRunner()

sample_data = {
    "top_tracks": [
        "[bold green]1[/bold green] - I Don't Know You by The Marías",
        "[bold green]2[/bold green] - Faucet by Earl  Sweatshirt",
        "[bold green]3[/bold green] - Fan by EST Gee",
        "[bold green]4[/bold green] - 2516 by Luna Li",
        "[bold green]5[/bold green] - Emotionless by Drake",
        "[bold green]6[/bold green] - Wat Be Wrong?? by Moneybagg Yo",
        "[bold green]7[/bold green] - Take Da Charge by Project Pat",
        "[bold green]8[/bold green] - I Know You by Faye Webster",
        "[bold green]9[/bold green] - Race by Alex G",
        "[bold green]10[/bold green] - Lick Back by EST Gee",
        "[bold green]11[/bold green] - Kingston by Faye Webster",
        "[bold green]12[/bold green] - TV by Alex G",
        "[bold green]13[/bold green] - 4K by El Alfa",
        "[bold green]14[/bold green] - Gabby (Vino24k Remix) by TisaKorean",
        "[bold green]15[/bold green] - Redemption by Drake",
        "[bold green]16[/bold green] - Senseless by Kodak Black",
        "[bold green]17[/bold green] - No Effort by Tee Grizzley",
        "[bold green]18[/bold green] - Exchange by Bryson Tiller",
        "[bold green]19[/bold green] - Los Infieles by Aventura",
        "[bold green]20[/bold green] - M.... She Wrote by Tay-K",
    ],
    "top_artists": [
        "[bold green]1[/bold green] - Drake - canadian hip hop, canadian pop, hip hop, pop rap, rap",
        "[bold green]2[/bold green] - Alex  - philly indie, pov: indie",
        "[bold green]3[/bold green] - Earl Sweatshirt - alternative hip hop, drumless hip hop, experimental hip hop, hip hop, rap, underground hip hop",
        "[bold green]4[/bold green] - Faye Webster - atlanta indie, indie pop",
        "[bold green]5[/bold green] - The Strokes - alternative rock, garage rock, modern rock, permanent wave, rock",
        "[bold green]6[/bold green] - Kanye West - chicago rap, hip hop, rap",
        "[bold green]7[/bold green] - Gunna - atl hip hop, melodic rap, rap, trap",
        "[bold green]8[/bold green] - El Alfa - dembow, rap dominicano, trap latino, urbano latino",
        "[bold green]9[/bold green] - Romeo Santos - bachata, latin hip hop, latin pop, urbano latino",
        "[bold green]10[/bold green] - Aventura - bachata, bachata dominicana, latin hip hop, latin pop, tropical, urbano latino",
        "[bold green]11[/bold green] - Lil Baby - atl hip hop, atl trap, rap, trap",
        "[bold green]12[/bold green] - Gutta100 - No genres found",
        "[bold green]13[/bold green] - Project Pat - crunk, dirty south rap, gangster rap, memphis hip hop, trap",
        "[bold green]14[/bold green] - Yo La Tengo - alternative rock, art pop, dream pop, indie rock, indietronica, lo-fi, new jersey indie, noise pop, permanent wave, shoegaze",
        "[bold green]15[/bold green] - EST Gee - kentucky hip hop, memphis hip hop, southern hip hop",
        "[bold green]16[/bold green] - Helmet - alternative metal, alternative rock, groove metal, grunge, industrial metal, industrial rock, nu metal, post-hardcore",
        "[bold green]17[/bold green] - Frank Ocean - lgbtq+ hip hop, neo soul",
        "[bold green]18[/bold green] - Nirvana - grunge, permanent wave, rock",
        "[bold green]19[/bold green] - Tay-K - cali rap, dfw rap, rap, trap",
        "[bold green]20[/bold green] - Yeat - pluggnb, rage rap",
    ],
    "track_duration": [
        209403,
        187746,
        158980,
        68000,
        302173,
        131005,
        186906,
        251666,
        223255,
        93799,
        202653,
        75524,
        201500,
        153704,
        333946,
        143857,
        193019,
        194613,
        257186,
        112000,
    ],
    "ms_to_minutes_seconds": [
        "3:29",
        "3:07",
        "2:38",
        "1:08",
        "5:02",
        "2:11",
        "3:06",
        "4:11",
        "3:43",
        "1:33",
        "3:22",
        "1:15",
        "3:21",
        "2:33",
        "5:33",
        "2:23",
        "3:13",
        "3:14",
        "4:17",
        "1:52",
    ],
    "search": {
        "track": {
            "tracks": {
                "items": [
                    {
                        "album": {
                            "album_type": "album",
                            "artists": [
                                {
                                    "name": "Weezer",
                                }
                            ],
                        },
                        "name": "Buddy Holly",
                    }
                ],
            }
        },
        "artist": {
            "artists": {
                "items": [
                    {
                        "genres": [
                            "alternative rock",
                            "modern power pop",
                            "modern rock",
                            "permanent wave",
                            "rock",
                        ],
                        "name": "Weezer",
                    }
                ]
            }
        },
    },
}


@pytest.fixture
def mock_spotify_client(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    client = SpotifyClient()
    client.authenticate = MagicMock(return_value="mock_auth")
    mocker.patch.object(
        client,
        "current_user_top_tracks",
        side_effect=lambda time_range=None, limit=None: sample_data["top_tracks"][
            :limit
        ],
    )
    mocker.patch.object(
        client,
        "current_user_top_artists",
        side_effect=lambda time_range=None, limit=None: sample_data["top_artists"][
            :limit
        ],
    )
    mocker.patch.object(
        client, "fetch_track_duration", return_value=sample_data["track_duration"]
    )
    mocker.patch.object(
        client,
        "search_spotify",
        side_effect=lambda query, authentication, limit, result_type: sample_data[
            "search"
        ][result_type],
    )
    return client


# Class method tests


def test_fetch_track_duration(mock_spotify_client: SpotifyClient):
    uri_list = [
        "spotify:track:06cqIVC8kRAT02qfHQT65v",
        "spotify:track:7KKW3MSfqCCai76gKSZEco",
        "spotify:track:5Yq99SJWqvNfr2cUYbrsNm",
        "spotify:track:0R6sz2EUOMSM3qaZHEpG63",
        "spotify:track:5Psnhdkyanjpgc2P8A5TSM",
        "spotify:track:2dTTzrWtpAN98pTYYRbMJB",
        "spotify:track:2XOKoaCWziW0W14DPeY7XS",
        "spotify:track:71BWZa1liIRyUiuJ3MB66o",
        "spotify:track:78bcWFqyuhOrC8wnkpgcft",
        "spotify:track:6P5ulGKtC4x6RnFbzfpq8O",
        "spotify:track:5WbfFTuIldjL9x7W6y5l7R",
        "spotify:track:5gnOGcUA9Thwa611bn3Rp2",
        "spotify:track:1BIXs6CdkPRLytuqoXs6XN",
        "spotify:track:3vM1zo5DGxNQbZVlmwAtzN",
        "spotify:track:4cRBqWBjuccCowYVHFlXK6",
        "spotify:track:3zzzVTaq2evjtfz4SryuaE",
        "spotify:track:6iF5JgF1GNUQwlnsgnMzUu",
        "spotify:track:43PuMrRfbyyuz4QpZ3oAwN",
        "spotify:track:0HDHY6RSHHG2ZTE0cMT4GJ",
        "spotify:track:1WRzux3cJRM9xRNN99QKgR",
    ]

    logging.debug("Test")
    result = mock_spotify_client.fetch_track_duration(
        authentication="mock_auth", track_uris=uri_list
    )
    assert result == sample_data["track_duration"]


def test_ms_to_minutes_and_seconds():
    result = SpotifyClient.ms_to_minutes_and_seconds(sample_data["track_duration"])
    assert result == sample_data["ms_to_minutes_seconds"]


@pytest.mark.parametrize(
    "limit, expected",
    [(None, sample_data["top_tracks"]), (1, sample_data["top_tracks"][:1])],
)
def test_current_user_top_tracks_tracklist(
    mock_spotify_client: SpotifyClient, limit: Literal[1] | None, expected: Any
):
    result = mock_spotify_client.current_user_top_tracks(limit=limit)
    assert result == expected


@pytest.mark.parametrize(
    "limit, expected",
    [(None, sample_data["top_artists"]), (1, sample_data["top_artists"][:1])],
)
def test_current_user_top_artists_artistlist(
    mock_spotify_client: SpotifyClient, limit: Literal[1] | None, expected: Any
):
    result = mock_spotify_client.current_user_top_artists(limit=limit)
    assert result == expected


# Typer command tests


def test_get_top_tracks_command(mock_spotify_client: SpotifyClient):
    with patch("src.spotify_cli.SpotifyClient", mock_spotify_client):
        result = runner.invoke(
            app,
            "get-top-tracks",
        )
        assert result.exit_code == 0


def test_get_top_artists_command(mock_spotify_client: SpotifyClient):
    with patch("src.spotify_cli.SpotifyClient", mock_spotify_client):
        result = runner.invoke(app, "get-top-artists")
        assert result.exit_code == 0


def test_search_tracks_command(mock_spotify_client: SpotifyClient):
    with patch("src.spotify_cli.SpotifyClient", mock_spotify_client):
        track_name = "Buddy Holly"
        artist_name = "Weezer"
        result = runner.invoke(app, ["search", "--track", track_name])

        assert result.exit_code == 0
        assert f'Results for "{track_name}":' in result.stdout
        assert f"1 - {track_name} by {artist_name}" in result.stdout


def test_search_artists_command(mock_spotify_client: SpotifyClient):
    with patch("src.spotify_cli.SpotifyClient", mock_spotify_client):
        artist_name = "Weezer"
        result = runner.invoke(app, ["search", "--artist", artist_name])

        assert result.exit_code == 0
        assert re.search(f'Results for "{artist_name}":', result.stdout)
        assert re.search("1 - Weezer - (?:.*rock.*)+", result.stdout)
