import re
from pathlib import Path

from models import Song, Song8d, get_session, AEP, Video, Channel
from paths import Dir

from utils import create_8d_song


with get_session() as session:
    channel: Channel = session.query(Channel).get(2)

print(channel.mro())

with get_session() as session:
    session.delete(channel)
    session.commit()