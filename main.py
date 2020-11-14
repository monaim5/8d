from sqlalchemy import or_, and_

from paths import Dir
from models import Song, get_session, Song8d, AEP, Video, RenderQueue

# songs = Song.all()
# print(songs)
# exit()
from utils import create_8d_song, create_aep, render_aep

songs = Dir.songs.value.glob('*.mp3')

"""adding songs to database"""
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

"""processing and rendering songs into 8D version"""
with get_session() as session:
    sub_query = session.query(Song8d.song_id)
    songs = session.query(Song).filter(~Song.id.in_(sub_query)).all()

    for song in songs:
        song_8d = create_8d_song(song)
        session.add(song_8d)
        session.commit()

"""
    creating adobe after effects projects
    from 8d songs where they have not rendered as video
    i.e : songs who have not a video
"""
with get_session() as session:
    render_queue = session.query(RenderQueue.aep_id)
    # return list of song_ids which the 8d song have aep but not approved
    aep_not_in_render_queue = session.query(AEP.song_8d_id).filter(AEP.id.notin_(render_queue))
    songs_not_in_render_queue = session.query(Song8d).filter(Song8d.id.in_(aep_not_in_render_queue)).all()

    aeps = session.query(AEP.song_8d_id)
    songs_havnt_aep = session.query(Song8d).filter(Song8d.id.notin_(aeps)).all()
    for song_8d in songs_not_in_render_queue:
        create_aep(song_8d)
        session.add(RenderQueue(song_8d.aep))
        session.commit()

    for song_8d in songs_havnt_aep:
        aep = AEP(song_8d)
        create_aep(song_8d)
        session.add(aep)
        session.flush()
        session.add(RenderQueue(aep))
        session.commit()

"""rendering adobe after effects projects"""
with get_session() as session:
    render_queue_items = session.query(RenderQueue).all()
    for item in render_queue_items:
        video = render_aep(item.aep)
        session.add(video)
        session.query(RenderQueue).filter(RenderQueue.id == item.id).delete()
        session.commit()
# upload_video(video)

