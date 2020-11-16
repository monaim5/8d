import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Date
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from paths import Dir, File, Other, Binary
from config import Database, Config
from mutagen.mp3 import MP3


Base = declarative_base()
engine = create_engine(f'sqlite:///{Binary.sqlite_db.value}')


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
    __title = Column('title', String, unique=True)
    __path = Column('path', String, unique=True)
    __duration = Column('duration', Numeric)
    song_8d = relationship("Song8d", uselist=False)

    def __init__(self, path: Path):
        self.__title = path.stem.__str__()
        self.__duration = get_mp3_duration(path)
        self.path = path

    @property
    def title(self):
        return self.__title

    @property
    def duration(self):
        return self.__duration

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    @classmethod
    def all(cls):
        with get_session() as session:
            return session.query(cls).all()

    def exists(self):
        with get_session() as session:
            return session.query(Song).filter(Song.__title == self.__title).scalar()


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
    song_id = Column(Integer, ForeignKey('songs.id'))
    __title = Column('title', String, unique=True)
    __path = Column('path', String, unique=True)

    song = relationship("Song", uselist=False)
    aep = relationship("AEP", uselist=False)

    def __init__(self, song: Song):
        self.__title = f'{song.title} [8D]'
        self.path = (Dir.songs_8d.value / self.__title).with_suffix('.mp3')
        self.flp_path = (Dir.flp.value / Config.durations.value[
            min(x for x in Config.durations.value if x > song.duration)])
        self.song = song

    @classmethod
    def var(cls):
        return cls._var

    @property
    def title(self):
        return self.__title

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


class AEP(Base):
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


class RenderQueue(Base):
    __tablename__ = 'render_queue'
    id = Column('id', Integer, primary_key=True)
    aep_id = Column(Integer, ForeignKey('aeps.id'))
    # priority = Column('priority', Integer)
    # added_date = Column('added_date', Date)
    aep = relationship("AEP", uselist=False)

    def __init__(self, aep: AEP):
        self.aep_id = aep.id


class Video(Base):
    __tablename__ = 'videos'
    id = Column('id', Integer, primary_key=True)
    aep_id = Column(Integer, ForeignKey('aeps.id'))
    __path = Column('path', String, unique=True)

    aep = relationship("AEP", uselist=False)
    upload_queue_item = relationship("UploadQueue", uselist=False)
    uploaded_video = relationship("UploadedVideo", uselist=False)

    def __init__(self, aep):
        self.aep_id = aep.id
        self.path = (Dir.videos.value / aep.song_8d.title).with_suffix('.mp4')

    @property
    def path(self):
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    def exists(self):
        return bool(self.path.stat().st_size) if self.path.exists() else False


class UploadQueue(Base):
    __tablename__ = 'upload_queue'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))

    video = relationship("Video", uselist=False)

    def __init__(self, video: Video):
        self.video_id = video.id


class UploadedVideo(Base):
    __tablename__ = 'uploaded_videos'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))

    video = relationship("Video", uselist=False)


class Channel:
    def __init__(self, name):
        self.name = name
        self.yt_credentials = File.lyrics_yt_credentials.value
        self.client_secrets = File.lyrics_client_secrets.value
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


def migrate():
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    migrate()
