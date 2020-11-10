from paths import songs_dir
from models import Song, get_session


songs = songs_dir.glob('*.mp3')

song = Song(songs_dir / 'shit.mp3')



print(song)

exit()
with get_session() as session:
    for song_path in songs:
        song = song(song_path)
        session.add(song)
    session.commit()


# song_8d = create_8d_song(song)
# aep = create_aep(_8d_song)
# video = render_aep(aep)
# upload_video(video)

