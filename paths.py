from pathlib import Path


root = Path(__file__).resolve().parent.parent
songs_dir = root / 'songs'
videos_dir = root / 'videos'
backgrounds_dir = root / 'backgrounds'
assets_dir = root / 'assets'
aep_temp_dir = assets_dir / 'aep/temp'
test_dir = root / 'test'


chrome_binary = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
chrome_driver = 'chromedriver.exe'
afterfx_com = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/afterfx.com'
aerender = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/aerender.exe'

json_bridge = assets_dir / 'bridge.json'
json_uploaded_to_lyrics = assets_dir / 'uploaded_to_lyrics.json'

lyrics_script_path = assets_dir / 'aep/scripts/to_lyrics.jsx'

# must be in database
lyrics_yt_credentials = assets_dir / 'credentials/lyrics_yt_credentials.json'
lyrics_client_secrets = assets_dir / 'credentials/lyrics_client_secrets.json'


