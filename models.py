import datetime
from ast import literal_eval
from pathlib import Path
from enum import Enum as NativeEnum
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Date, Time, Enum, ARRAY, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from paths import Dir, File, Other, Binary
from config import Database, Config
from mutagen.mp3 import MP3


Base = declarative_base()
engine = create_engine(f'sqlite:///{Binary.sqlite_db.value}')

__all__ = [
    'get_session',
    'Song',
    'Song8d',
    'AEP',
    'RenderQueue',
    'Video',
    'UploadQueue',
    'UploadedVideo',
    'Channel',
]


class WeekDays(NativeEnum):
    mon = 0
    tue = 1
    wed = 2
    thu = 3
    fri = 4
    sat = 5
    sun = 6


class get_session:
    def __enter__(self):
        self.session = sessionmaker(bind=engine)()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()


def get_mp3_duration(path):
    audio = MP3(path)
    return audio.info.length


class MyBase:
    def add(self, session, *, flush=False, commit=False):
        session.add(self)
        session.flush() if flush else None
        session.commit() if commit else None

    def delete(self, session, *, flush, commit):
        session.delete(self)
        session.flush() if flush else None
        session.commit() if commit else None


class Song(Base, MyBase):
    __tablename__ = 'songs'
    id = Column('id', Integer, primary_key=True)
    title = Column('title', String, unique=True)
    __path = Column('path', String, unique=True)
    duration = Column('duration', Numeric)
    song_8d = relationship("Song8d", uselist=False)

    def __init__(self, path: Path):
        self.title = path.stem.__str__()
        self.duration = get_mp3_duration(path)
        self.path = path

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    def exists(self):
        with get_session() as session:
            return session.query(Song).filter(Song.title == self.title).scalar()


class Song8d(Base, MyBase):
    __tablename__ = 'songs_8d'
    id = Column('id', Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.id'))
    title = Column('title', String, unique=True)
    __path = Column('path', String, unique=True)

    song = relationship("Song", uselist=False)
    aep = relationship("AEP", uselist=False)

    def __init__(self, song: Song):
        self.title = f'{song.title} [8D]'
        self.song_id = song.id
        self.path = (Dir.songs_8d.value / self.title).with_suffix('.mp3')
        self.flp_path = (Dir.flp.value / Config.durations.value[
            min(x for x in Config.durations.value if x > song.duration)])

    @property
    def path(self):
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    @property
    def flp_path(self) -> Path:
        return Dir.root.value / self.__flp_path

    @flp_path.setter
    def flp_path(self, value: Path):
        self.__flp_path = value.relative_to(Dir.root.value).__str__()


class AEP(Base, MyBase):
    __tablename__ = 'aeps'
    id = Column('id', Integer, primary_key=True)
    song_8d_id = Column(Integer, ForeignKey('songs_8d.id'))
    __path = Column('path', String, unique=True)

    song_8d = relationship("Song8d", uselist=False)
    video = relationship("Video", uselist=False)
    render_queue_item = relationship("RenderQueue", uselist=False)

    def __init__(self, song_8d: Song8d):
        self.song_8d_id = song_8d.id
        self.path = (Dir.aep_temp.value / song_8d.title).with_suffix('.aep')

    @property
    def path(self):
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()


class RenderQueue(Base, MyBase):
    __tablename__ = 'render_queue'
    id = Column('id', Integer, primary_key=True)
    aep_id = Column(Integer, ForeignKey('aeps.id'))
    # priority = Column('priority', Integer)
    # added_date = Column('added_date', Date)
    aep = relationship("AEP", uselist=False)

    def __init__(self, aep: AEP):
        self.aep_id = aep.id


class Video(Base, MyBase):
    __tablename__ = 'videos'
    id = Column('id', Integer, primary_key=True)
    title = Column('title', String)
    aep_id = Column(Integer, ForeignKey('aeps.id'))
    __path = Column('path', String, unique=True)

    aep = relationship("AEP", uselist=False)
    upload_queue_item = relationship("UploadQueue", uselist=False)
    uploaded_video = relationship("UploadedVideo", uselist=False)

    def __init__(self, aep):
        self.aep_id = aep.id
        self.path = (Dir.videos.value / aep.song_8d.title).with_suffix('.mp4')
        self.title = aep.song_8d.title

    @property
    def path(self):
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    def exists(self):
        return bool(self.path.stat().st_size) if self.path.exists() else False


class Channel(Base, MyBase):
    __tablename__ = 'channels'
    id = Column('id', Integer, primary_key=True)
    yt_channel_id = Column('yt_channel_id', String)
    name = Column('name', String)
    __yt_credentials = Column('yt_credentials', String)
    __client_secrets = Column('client_secrets', String)
    category = Column('category', String)
    publish_time = Column('publish_time', Time)
    __publish_days = Column('publish_days', String)

    uploaded_videos = relationship("UploadedVideo")
    upload_queue_items = relationship("UploadQueue")

    def __init__(self, name):
        self.name = name
        self.yt_channel_id = 'UCaVHqBYCGSXbSfXVv0EcLxw'
        self.yt_credentials = File.lyrics_yt_credentials.value
        self.client_secrets = File.lyrics_client_secrets.value
        self.category = 'Music'
        self.publish_time = datetime.time(15, 0, 0)
        self.publish_days = [WeekDays.tue.name, WeekDays.thu.name, WeekDays.sat.name]

    @property
    def yt_credentials(self) -> Path:
        return Dir.root.value / self.__yt_credentials

    @yt_credentials.setter
    def yt_credentials(self, value: Path):
        self.__yt_credentials = value.relative_to(Dir.root.value).__str__()

    @property
    def client_secrets(self) -> Path:
        return Dir.root.value / self.__client_secrets

    @client_secrets.setter
    def client_secrets(self, value: Path):
        self.__client_secrets = value.relative_to(Dir.root.value).__str__()

    @property
    def publish_days(self) -> List[WeekDays]:
        return list(map(lambda x: WeekDays.__getitem__(x), literal_eval(self.__publish_days)))

    @publish_days.setter
    def publish_days(self, value: List[WeekDays]):
        self.__publish_days = str(value)

    def latest_published_date(self, session) -> datetime:
        return session.query(func.max(UploadedVideo.published_date)) \
            .filter(UploadedVideo.channel_id == self.id).one()[0]

    def next_publish_date(self, session) -> datetime:
        def get_days_ahead_from_to(date: datetime, weekday: int):
            days_ahead = weekday - date.weekday()
            return days_ahead if days_ahead >= 0 else 6 + days_ahead

        def get_publish_date_according_to(date: datetime):
            publish_days = (day.value for day in self.publish_days)
            days_ahead = min([get_days_ahead_from_to(date, days) for days in publish_days])
            return date + datetime.timedelta(days=days_ahead)

        today = datetime.datetime.now()
        today = today.date() if today.time() < self.publish_time else today.date() + datetime.timedelta(days=1)
        latest_published_date = self.latest_published_date(session)

        if latest_published_date is None or latest_published_date < get_publish_date_according_to(today):
            publish_at = datetime.datetime.combine(get_publish_date_according_to(today), self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)
        else:
            publish_at = datetime.datetime.combine(get_publish_date_according_to(latest_published_date),
                                                   self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)

        return publish_at


class UploadQueue(Base, MyBase):
    __tablename__ = 'upload_queue'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    channel_id = Column(Integer, ForeignKey('channels.id'))

    video = relationship("Video", uselist=False)
    channel = relationship("Channel", uselist=False)

    def __init__(self, video: Video, channel: Channel):
        self.channel_id = channel.id
        self.video_id = video.id


class UploadedVideo(Base, MyBase):
    __tablename__ = 'uploaded_videos'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    title = Column('title', String)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    yt_video_id = Column('youtube_id', String)
    published_date = Column('published_date', Date)

    video = relationship("Video", uselist=False)
    channel = relationship("Channel", uselist=False)

    def __init__(self, video, channel):
        self.video_id = video.id
        self.channel_id = channel.id


def migrate():
    Base.metadata.create_all(bind=engine)


def main():
    migrate()
    channel = Channel('8d')
    with get_session() as session:
        session.add(channel)
        session.commit()


if __name__ == '__main__':
    main()
