from paths import Dir
from models import Song, get_session, Song8d

# songs = Song.all()
# print(songs)
# exit()
from utils import create_8d_song

songs = Dir.songs.value.glob('*.mp3')

with get_session() as session:
    added_songs = 0
    for song_path in songs:
        song = Song(song_path)
        if song.exists():
            continue
        session.add(song)
        added_songs += 1
    session.commit()
    print(f'{added_songs} song has been added to database')

with get_session() as session:
    sub_query = session.query(Song8d.id)
    songs = session.query(Song).filter(~Song.id.in_(sub_query)).all()

    for song in songs:
        song_8d = create_8d_song(song)
        session.add(song_8d)
        session.commit()


# song_8d = create_8d_song(song)
# aep = create_aep(_8d_song)
# video = render_aep(aep)
# upload_video(video)

