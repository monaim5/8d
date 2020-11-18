import re

from models import Song, Song8d, get_session
from paths import Dir

from utils import create_8d_song

with get_session() as session:
    songs = session.query(Song).all()

    for song in songs:
        title = re.sub('[0-9]*\. ', '', song.title)
        song.title = 'Ariana grande - ' + title
    session.commit()





