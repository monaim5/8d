import shutil

from paths import Dir
from models import *
from multiprocessing import Process, Condition, Queue

from utils import *
from youtube_metadata import *


def register_songs_process(session):
    """adding songs to database. songs located in songs directory
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    """
    songs = Dir.songs.value.glob('*.mp3')
    added_songs = 0
    for song_path in songs:
        song = Song(song_path)
        if song.exists():
            continue
        song.add(session, flush=False, commit=True)
        added_songs += 1
    print(f'{added_songs} song has been added to database')


def register_backgrounds_process(session):
    backgrounds = Dir.backgrounds.value.glob('*.jpg')
    backgrounds_added = 0
    for background_path in backgrounds:
        background = Background(background_path)
        if background.exists():
            continue
        background.add(session, flush=False, commit=True)
        backgrounds_added += 1
    print(f'{backgrounds_added} background has been added to database')


def convert_to_8ds_process(session):
    """
    processing and rendering songs into 8D version
    1 - get songs from database
    2 - creating 8d song and export it into 8d_songs directory as .mp3 file
    3 - ad 8d song to database
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    """
    sub_query = session.query(Song8d.song_id)
    songs = session.query(Song).filter(~Song.id.in_(sub_query)).all()

    for song in songs:
        create_8d_song(song).add(session, flush=False, commit=True)


def create_aeps_process(session):
    """
    creating adobe after effects projects (aep) from 8d songs :
    which they have an aep but not rendered as video and not in render queue
        -> [query used : songs_not_in_rq_and_vid]
    which basically have not an aep
        -> [query used : songs_havnt_aep]
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    """
    # aep_in_rq = session.query(RenderQueue.aep_id)
    # return list of song_ids which the 8d song have aep but not approved
    # aep_rendered = session.query(Video.aep_id)
    # aep_not_in_rq_and_vid = session.query(AEP.song_8d_id).filter(AEP.id.notin_(aep_in_rq)) \
    #                                                      .filter(AEP.id.notin_(aep_rendered))
    # songs_not_in_rq_and_vid = session.query(Song8d).filter(Song8d.id.in_(aep_not_in_rq_and_vid)).all()

    # for song_8d in songs_not_in_rq_and_vid:
    #     create_aep(song_8d, background, color)
    #     RenderQueue(song_8d.aep).add(session, flush=False, commit=True)

    aeps = session.query(AEP.song_8d_id)
    songs_havnt_aep = session.query(Song8d).filter(Song8d.id.notin_(aeps)).all()

    bg_used = session.query(AEP.background_id)
    backgrounds = session.query(Background).filter(Background.id.notin_(bg_used))
    for song_8d, background in zip(songs_havnt_aep, backgrounds):
        color = Color.get_random()
        aep = create_aep(song_8d, background, color)
        aep.add(session, flush=True, commit=False)
        RenderQueue(aep).add(session, flush=False, commit=True)


def render_aeps_process(session, queue: Queue, condition: Condition):
    """
    rendering adobe after effects projects (aep) and adding rendered videos to upload queue
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    :param queue: The upload queue that used by the func upload_video_process it contains videos.
    :type queue: multiprocessing.Queue
    :param condition: by this param we can resumed upload process (separate process)
                      which may be waiting for videos to add to upload queue
    :type condition: multiprocessing.Condition

    1 - get render queue from database
    2 - render aep and export it into videos folder as an .mp4 file
    3 - add rendered video to database
    4 - add it to upload_queue table in database
    5 - delete his corresponding item in render queue
    6 - add it to the local upload_queue
    7 - notify the upload queue process that we added a video into his queue
    """
    render_queue_items = session.query(RenderQueue).all()
    channel = session.query(Channel).filter(Channel.name == '8d').one()
    print(f'{len(render_queue_items)} item in render queue')
    for item in render_queue_items:
        video = render_aep(item.aep)
        video.add(session, flush=True, commit=False)

        item.aep.background.archive(session)
        item.aep.song_8d.archive(session)
        item.aep.song_8d.song.archive(session)

        upload_queue_item = UploadQueue(video, channel)
        upload_queue_item.add(session, flush=True, commit=True)
        queue.put((upload_queue_item.video, channel))
        item.delete(session, flush=False, commit=True)
        with condition:
            condition.notify_all()


def upload_video_process(upload_queue: Queue, condition: Condition):
    """Upload videos in queue one by one
    :param upload_queue: The queue which we will use for uploading videos
    :type upload_queue: multiprocessing.Queue
    :param condition: this param Condition we will use it for make the upload process
                      wait if there is no more videos in queue
                      or resume it after we added videos to queue, where it was waiting
    :type condition: multiprocessing.Condition
    """
    video_index = 1
    with get_session() as session:
        while True:
            if upload_queue.empty():
                with condition:
                    print('waiting for videos to upload')
                    condition.wait()

            upload_queue_item = upload_queue.get()
            if upload_queue_item is None:
                print('upload videos done')
                return

            video, channel = upload_queue_item
            try:
                print(f'uploading the {video_index} video')
                uploaded_video = upload_video(video, channel,
                                              title=generate_title(video.title),
                                              description=generate_desc(video.title),
                                              tags=generate_tags(video.title),
                                              publish_at=channel.next_publish_date(session))
                uploaded_video.add(session=session, commit=True)
                session.query(UploadQueue).filter(UploadQueue.video_id == video.id).delete()
                session.commit()
                video_index += 1
            except ConnectionResetError as e:
                print(e.__class__)
                print(e)


def main():
    queue = Queue()
    condition = Condition()

    with get_session() as session:
        uploading_process = Process(target=upload_video_process, args=(queue, condition))
        upload_queue = session.query(UploadQueue).all()

        for item in upload_queue:
            queue.put((item.video, item.channel))

        uploading_process.start()

        try:
            register_songs_process(session)
            register_backgrounds_process(session)
            convert_to_8ds_process(session)
            create_aeps_process(session)
            render_aeps_process(session=session, queue=queue, condition=condition)

        finally:
            queue.put(None)
            with condition:
                condition.notify_all()


if __name__ == '__main__':
    main()
