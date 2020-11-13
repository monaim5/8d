from enum import Enum
from pathlib import Path


class Dir(Enum):
    root = Path(__file__).resolve().parent.parent
    songs = root / 'songs'
    songs_8d = root / '8d_songs'
    videos = root / 'videos'
    backgrounds = root / 'backgrounds'
    assets = root / 'assets'
    bin = root / 'bin'
    aep_temp = assets / 'aep/temp'
    flp = assets / 'flp'
    test = root / 'test'


class Binary(Enum):
    sqlite_db = Dir.bin.value / '8d.db'
    chrome_driver = Dir.bin.value / 'chromedriver.exe'
    chrome_binary = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    fl_studio = r'C:\Program Files (x86)\Image-Line\FL Studio 20\FL.exe'
    afterfx_com = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/afterfx.com'
    aerender = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/aerender.exe'


class File(Enum):
    json_bridge = Dir.assets.value / 'bridge.json'
    json_uploaded_to_lyrics = Dir.assets.value / 'uploaded_to_lyrics.json'
    lyrics_script_path = Dir.assets.value / 'aep/scripts/to_lyrics.jsx'
    # must be in database
    lyrics_yt_credentials = Dir.assets.value / 'credentials/lyrics_yt_credentials.json'
    lyrics_client_secrets = Dir.assets.value / 'credentials/lyrics_client_secrets.json'


class Other(Enum):
    flp_song = Dir.flp.value / 'song.mp3'


def init_paths():
    for d in Dir:
        if not d.value.exists():
            d.value.mkdir(parents=True)

    for f in File:
        if not f.value.exists():
            try:
                f.value.touch()
            except FileNotFoundError as e:
                f.value.parent.mkdir(parents=True, exist_ok=True)
                f.value.touch()


init_paths()
