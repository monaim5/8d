import time

from paths import Dir
from models import Song, get_session, Song8d, AEP, Video, RenderQueue, UploadQueue
from multiprocessing import Process, Condition, Queue


from utils import create_8d_song, create_aep, render_aep, upload_video


def register_songs_process():
    """adding songs to database. songs located in songs directory"""
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


def convert_to_8ds_process():
    """
    processing and rendering songs into 8D version
    1 - get songs from database
    2 - creating 8d song and export it into 8d_songs directory as .mp3 file
    3 - ad 8d song to database
    """
    with get_session() as session:
        sub_query = session.query(Song8d.song_id)
        songs = session.query(Song).filter(~Song.id.in_(sub_query)).all()

        for song in songs:
            song_8d = create_8d_song(song)
            session.add(song_8d)
            session.commit()


def create_aeps_process():
    """
    creating adobe after effects projects (aep) from 8d songs :
    which they have an aep but not rendered as video and not in render queue
        -> [query used : songs_not_in_rq_and_vid]
    which basically have not an aep
        -> [query used : songs_havnt_aep]
    """
    with get_session() as session:
        aep_in_rq = session.query(RenderQueue.aep_id)
        # return list of song_ids which the 8d song have aep but not approved
        aep_rendered = session.query(Video.aep_id)
        aep_not_in_rq_and_vid = session.query(AEP.song_8d_id).filter(AEP.id.notin_(aep_in_rq)) \
                                                             .filter(AEP.id.notin_(aep_rendered))
        songs_not_in_rq_and_vid = session.query(Song8d).filter(Song8d.id.in_(aep_not_in_rq_and_vid)).all()

        aeps = session.query(AEP.song_8d_id)
        songs_havnt_aep = session.query(Song8d).filter(Song8d.id.notin_(aeps)).all()

        for song_8d in songs_not_in_rq_and_vid:
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


def render_aeps_process(queue: Queue, condition: Condition):
    """
    rendering adobe after effects projects (aep) and adding rendered videos to upload queue
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
    with get_session() as session:
        render_queue_items = session.query(RenderQueue).all()
        for item in render_queue_items:
            video = render_aep(item.aep)
            session.add(video)
            session.flush()
            session.add(UploadQueue(video))
            session.flush()
            session.delete(item)
            queue.put(video)
            with condition:
                condition.notify_all()
            session.commit()


def upload_video_process(upload_queue: Queue, condition: Condition):
    # TODO: Test upload_queue items if they can deal another database session
    #       (for deleting upload queue item) and (add video to uploaded_videos)
    # TODO: Implement the upload_video function
    # TODO: Add database process when upload complete
    """
    Upload videos in queue one by one
    :param upload_queue: The queue which we will use for uploading videos
    :type upload_queue: multiprocessing.Queue
    :param condition: this param Condition we will use it for make the upload process
                      wait if there is no more videos in queue
                      or resume it after we added videos to queue, where it was waiting
    :type condition: multiprocessing.Condition
    """
    while True:
        video = upload_queue.get()
        if video is None:
            print('upload video process shutdown')
            return
        print(f'process for video {video}')
        time.sleep(5)
        print(f'video {video["title"]} has uploaded')
        if upload_queue.empty():
            with condition:
                print('waiting for other videos')
                condition.wait()


def main():

    queue = Queue()
    condition = Condition()
    uploading_process = Process(target=upload_video_process, args=(queue, condition))

    with get_session() as session:
        upload_queue = session.query(UploadQueue).all()
    for item in upload_queue:
        queue.put(item.video)

    uploading_process.start()

    register_songs_process()
    convert_to_8ds_process()
    create_aeps_process()
    render_aeps_process(queue=queue, condition=condition)

    queue.put(None)
    with condition:
        condition.notify_all()


if __name__ == '__main__':
    main()
