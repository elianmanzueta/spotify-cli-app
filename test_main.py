import unittest
from unittest.mock import patch, MagicMock
from main import SpotifyClient


class TestSpotifyClient(unittest.TestCase):
    """
    Test Class to test the SpotifyClient class.
    """

    def setUp(self):
        self.client = SpotifyClient()
        self.mock_session = MagicMock()
        # Patch instance method of SpotifyClient
        self.patcher = patch.object(
            self.client, "session_constructor", return_value=self.mock_session
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_current_user_top_tracks_returns_formatted_string(self):
        """
        Test the output of the current_user_top_tracks function.
        """
        self.mock_session.current_user_top_tracks.return_value = {
            "items": [{"name": "Buddy Holly", "artists": [{"name": "Weezer"}]}]
        }

        result = self.client.current_user_top_tracks()
        self.assertEqual(result, ["[bold green]1[/bold green] - Buddy Holly by Weezer"])

    def test_current_user_top_tracks_handles_empty_response(self):
        """
        Test current_user_top_tracks with an empty API response.
        """
        # Configure the mock to return an empty list
        self.mock_session.current_user_top_tracks.return_value = {"items": []}

        result = self.client.current_user_top_tracks()
        self.assertEqual(result, [])  # Expect an empty list as a result


if __name__ == "__main__":
    unittest.main()
