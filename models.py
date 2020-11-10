import datetime
from abc import ABC
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from paths import aep_temp_dir, videos_dir, lyrics_client_secrets, lyrics_yt_credentials
from config import Database
from mutagen.mp3 import MP3

Base = declarative_base()
engine = create_engine('sqlite:///8d.db', echo=True)


def migrate():
    Base.metadata.create_all(bind=engine)


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


class Song(Base):
    __tablename__ = 'songs'
    id = Column('id', Integer, primary_key=True)
    title = Column('title', String, unique=True)
    path = Column('path', String, unique=True)
    duration = Column('duration', Numeric)
    song_8d = relationship("Song8d", uselist=False, back_populates="song")

    def __init__(self, path):
        self.title = path.stem
        self.path = path
        self.duration = get_mp3_duration(path)

    @classmethod
    def all(cls):
        with get_session() as session:
            session.query(cls).all()

    # @classmethod
    # def get_un8d_songs(cls):
    #     with get_session() as session:
    #         session.query(cls).notin(Song8d)

    # def get_unrendered_songs(self):
    #     with get_session() as session:
    #         session.query()


    # def __init__(self, song_path: Path):
    #     self.id = input('This song\'s id is : ')
    #     self.path = song_path
    #
    #     self.save_or_get()

    # @property
    # def video_path(self):
    #     return videos_dir / (self.title + '.mp4')
    #
    # @property
    # def aep_path(self):
    #     return aep_temp_dir / (self.title + ' [lyrics].aep')
    #
    # @property
    # def has_video(self):
    #     return bool(self.video_path.stat().st_size) if self.video_path.exists() else False
    #
    # @property
    # def has_aep(self):
    #     return self.aep_path.exists()
    #
    # def save_or_get(self):
    #     pass
    #
    # def save(self):
    #     conn = db.get_connection()
    #     cur = conn.cursor()
    #     cur.execute(f'INSERT INTO {self.table} VALUES (?)',  (self.title,))


class Song8d(Base):
    __tablename__ = 'songs_8d'
    id = Column('id', Integer, primary_key=True)
    path = Column('path', String, unique=True)
    song_id = Column(Integer, ForeignKey('songs.id'))

    song = relationship("Song", uselist=False, back_populates="song_8d")
    aep = relationship("AEP", uselist=False, back_populates="song_8d")


class AEP(Base):
    __tablename__ = 'aeps'
    id = Column('id', Integer, primary_key=True)
    path = Column('path', String, unique=True)
    song_8d_id = Column(Integer, ForeignKey('songs_8d.id'))

    song_8d = relationship("Song8d", uselist=False, back_populates="aep")
    video = relationship("Video", uselist=False, back_populates="aep")


class Video(Base):
    __tablename__ = 'videos'
    id = Column('id', Integer, primary_key=True)
    path = Column('path', String, unique=True)
    aep_id = Column(Integer, ForeignKey('aeps.id'))

    aep = relationship("AEP", uselist=False, back_populates="video")
    upload_queue_item = relationship("UploadQueue", uselist=False, back_populates="video")
    uploaded_video = relationship("UploadedVideo", uselist=False, back_populates="video")


class UploadQueue(Base):
    __tablename__ = 'upload_queue'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))

    video = relationship("Video", uselist=False, back_populates="upload_queue_item")


class UploadedVideo(Base):
    __tablename__ = 'uploaded_videos'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))

    video = relationship("Video", uselist=False, back_populates="uploaded_video")


class Channel:
    def __init__(self, name):
        self.name = name
        self.yt_credentials = lyrics_yt_credentials
        self.client_secrets = lyrics_client_secrets
        self.category = 'Music'
        self.publish_time = datetime.time(15, 0, 0)
        self.publish_days = {1, 3, 5}

    @property
    def latest_published_date(self) -> datetime:
        cur = db.get_connection().cursor()
        return cur.execute('SELECT max(publish_date) as date FROM `uploaded_to_lyrics`'
                           'where channel_name = ?', (self.name,)).fetchone()[0]

    def next_publish_date(self):
        def get_days_ahead_from_to(date: datetime, weekday: int):
            days_ahead = weekday - date.weekday()
            return days_ahead if days_ahead >= 0 else 6 + days_ahead

        def get_publish_date_according_to(date: datetime):
            days_ahead = min([get_days_ahead_from_to(date, days) for days in self.publish_days])
            return date + datetime.timedelta(days=days_ahead)

        today = datetime.datetime.now()
        today = today.date() if today.time() < self.publish_time else today.date() + datetime.timedelta(days=1)

        if self.latest_published_date is None or self.latest_published_date < get_publish_date_according_to(today):
            publish_at = datetime.datetime.combine(get_publish_date_according_to(today), self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)
        else:
            publish_at = datetime.datetime.combine(get_publish_date_according_to(self.latest_published_date),
                                                   self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)

        return publish_at


if __name__ == '__main__':
    migrate()