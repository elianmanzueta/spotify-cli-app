# Spotify CLI App

[![CodeFactor](https://www.codefactor.io/repository/github/elianmanzueta/spotify-cli-app/badge/main)](https://www.codefactor.io/repository/github/elianmanzueta/spotify-cli-app/overview/main) [![Maintainability](https://api.codeclimate.com/v1/badges/4146453dcc13ff14ea59/maintainability)](https://codeclimate.com/github/elianmanzueta/spotify-cli-app/maintainability) ![example workflow](https://github.com/elianmanzueta/spotify-cli-app/actions/workflows/workflow.yml/badge.svg)

## Overview

This app is a Python-based command-line interface that allows users to interact with the Spotify Web API. It enables you to retrieve your top songs and artists, and search for tracks and artists on Spotify.

## Features

- **Get Top Songs and Artists**: Easily access your favorite songs and artists based on your Spotify listening history. Similar to projects like Receiptify.
- **Search Functionality**: Search for tracks and artists directly from the command line.

## Installation

Requires Python >= 3.12

1. Clone the repository:

   ```git clone https://github.com/elianmanzueta/spotify-cli-app.git```

2. Navigate to the app directory:

    `cd spotify-cli-app`

3. Install dependencies:

    `pip install -r requirements.txt`

## Usage

![Help](images/Help%20page.png)

### Get your top tracks

`python src/spotify_cli.py get-top-tracks`

Options include:

- Limit
- Time range

![Top Songs](images/Top%20Songs.png)

#### Get top tracks with options

`python src/spotify_cli.py get-top-tracks --limit 5 --time-range short_term`

![Top Songs With Options](images/Top%20Songs%20with%20Options.png)

### Get your top artists

`python src/spotify_cli.py get-top-artists`

Options include:

- Limit
- Time range

![Top Artists](images/Top%20Artists.png)

#### Get top artists with options

`python src/spotify_cli.py get-top-artists --limit 6 --time-range long_term`

![Top Artists With Options](images/Top%20Artists%20with%20Options.png)

### Search

#### Search for Artists

`python src/spotify_cli.py search --artist "Weezer"`

![Search Artists](images/Search%20-%20Artists.png)

#### Search for Tracks

`python src/spotify_cli.py search --track "Buddy Holly"`

![Search Tracks](images/Search%20-%20Tracks.png)

## Configuration

Before using the app, you'll need to set up your Spotify API credentials.

Create a [Spotify Developer](https://developer.spotify.com) account and create a new application. 

Go to your app's settings and get the Client ID, Client Secret, and Redirect URI.

Add your Client ID, Client Secret, and Redirect URI to a .env file in the project root.

## License

Distributed under the MIT License. See LICENSE for more information.
