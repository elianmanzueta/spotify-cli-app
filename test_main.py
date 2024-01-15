import unittest
from unittest.mock import patch
from main import SpotifyClient  # Adjust the import as per your project structure

class TestSpotifyClient(unittest.TestCase):

    @patch('main.SpotifyClient.session_constructor')
    def test_current_user_top_tracks(self, mock_session):
        # Mock the session constructor and Spotify API responses
        mock_session.return_value.current_user_top_tracks.return_value = {'items': [{'name': 'Song1', 'artists': [{'name': 'Artist1'}]}]}

        client = SpotifyClient()
        result = client.current_user_top_tracks()
        self.assertEqual(result, ['Song1 - Artist1'], f"{result} not ['Song1 - Artist1']")

# Add more test cases...

if __name__ == '__main__':
    unittest.main()
