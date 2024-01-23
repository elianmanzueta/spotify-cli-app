# Spotify CLI App

## Overview
This app is a Python-based command-line interface that allows users to interact with the Spotify Web API. It enables you to retrieve your top songs and artists, and search for tracks and artists on Spotify.

## Features
- **Get Top Songs and Artists**: Easily access your favorite songs and artists based on your Spotify listening history. Similar to projects like Receiptify.
- **Search Functionality**: Search for tracks and artists directly from the command line.

## Installation
1. Clone the repository:

   ```git clone https://github.com/elianmanzueta/spotify-cli-app.git```

2. Navigate to the app directory:
    
    `cd spotify-cli-app`

3. Install dependencies:

    `pip install -r requirements.txt`

## Usage

![Help](images/Help%20page.png)

### Get your top songs

`python main.py get-top-songs`

Options include:
- Limit 
- Time range

![Top Songs](images/Top%20Songs.png)

#### With options

`python main.py get-top-songs --limit 5 --time-range short_term`

![Top Songs With Options](images/Top%20Songs%20with%20Options.png)

### Get your top artists

`python main.py get-top-artists`

Options include:
- Limit
- Time range

![Top Artists](images/Top%20Artists.png)

#### With options

`python main.py get-top-artists --limit 6 --time-range long_term`

![Top Artists With Options](images/Top%20Artists%20with%20Options.png)

### Search 

#### Search for Artists

`python main.py search --artist "Weezer"`

![Search Artists](images/Search%20-%20Tracks.png)

#### Search for Tracks

`python main.py search --track "Buddy Holly"`

![Search Tracks](images/Search%20-%20Tracks.png)

## Configuration

Before using the app, you'll need to set up your Spotify API credentials.

Create a [Spotify Developer](https://developer.spotify.com) account and create a new application.

Add your Client ID and Client Secret to a .env file in the project root.

## License

Distributed under the MIT License. See LICENSE for more information.