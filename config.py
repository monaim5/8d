import json
import sqlite3
from enum import Enum
from random import choice

from paths import Dir, File


class Config(Enum):
    durations = {
        160: '8D_160.flp',
        180: '8D_180.flp',
        210: '8D_210.flp',
        240: '8D_240.flp',
        360: '8D_360.flp'
    }

    # colors = {
    #     'red': '#9c0000',
    #     'red_light': '#eb6767',
    #     'green': '#007d0a',
    #     'green_light': '#4ab553',
    #     'blue': '#0000ab',
    #     'blue_light': '##5454ff',
    #     'yellow': '#b5ac00',
    #     'yellow_light': '#fff64f',
    #     'cyan': '#009485',
    #     'cyan_light': '#49fcea',
    #     'purple': '#8a0087',
    #     'purple_light': '#d65ed4',
    #
    # }

    headers = {
        "Host": "www.musixmatch.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Upgrade-Insecure-Requests": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    }


class Color(Enum):
    red = '#9c0000'
    red_light = '#eb6767'
    green = '#007d0a'
    green_light = '#4ab553'
    blue = '#0000ab'
    blue_light = '##5454ff'
    yellow = '#b5ac00'
    yellow_light = '#fff64f'
    cyan = '#009485'
    cyan_light = '#49fcea'
    purple = '#8a0087'
    purple_light = '#d65ed4'

    @classmethod
    def get_random(cls):
        return choice(list(cls))


class Bcolors(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Database:
    def __init__(self, db):
        self.__connection = None
        self.host = Dir.root.value / f'databases/{db}.db'

    def get_connection(self):
        if self.__connection is not None:
            print("already connected to database")
            return self.__connection
        else:
            # try:
            self.__connection = sqlite3.connect(self.host)
            print("Connecting to database")
            return self.__connection
            # except pymysql.err.InternalError:
            #     config_database()
            #     return get_connection()

    def config_database(self):
        cursor = self.get_connection()
        cursor.execute('CREATE TABLE IF NOT EXISTS songs ('
                       'id VARCHAR(20) PRIMARY KEY,'
                       'title VARCHAR(255) UNIQUE,'
                       'duration INTEGER(3))')

        cursor.execute('CREATE TABLE IF NOT EXISTS videos ('
                       'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                       'song_id VARCHAR(20),'
                       'FOREIGN KEY(song_id) REFERENCES songs(id))')

        cursor.execute('CREATE TABLE IF NOT EXISTS uploaded_to_8d ('
                       'song_id VARCHAR(20) PRIMARY KEY,'
                       'video_id INTEGER,'
                       'uploaded_id VARCHAR(20),'
                       'title VARCHAR(255),'
                       'channel_name VARCHAR(255),'
                       'channel_id VARCHAR(255),'
                       'publish_date DATE DEFAULT NULL,'
                       'FOREIGN KEY(video_id) REFERENCES videos(id))')

        cursor.execute('CREATE TABLE IF NOT EXISTS upload_queue ('
                       'video_id INTEGER PRIMARY KEY,'
                       'FOREIGN KEY(video_id) REFERENCES videos(id))')

        # cursor.execute('CREATE TABLE IF NOT EXISTS colors('
        #                'name VARCHAR(20) PRIMARY KEY,'
        #                'code VARCHAR(7) NOT NULL )')
        #
        # cursor.execute('CREATE TABLE IF NOT EXISTS users('
        #                'name VARCHAR(255) PRIMARY KEY,'
        #                'race VARCHAR(255) NOT NULL,'
        #                'email VARCHAR(255),'
        #                'password VARCHAR(255),'
        #                'channel_id VARCHAR(255),'
        #                'nb_accounts INT,'
        #                'client_secrets_path VARCHAR(255),'
        #                'token_path VARCHAR(255)),'
        #                'purpose VARCHAR(40)')
        self.get_connection().commit()
        print("create database")


#
#
#
# def close_connection():
#     global CONNECTION
#     if CONNECTION is not None:
#         CONNECTION.close()


def configure_data():
    db = Database('ncs_arabi')
    db.config_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    with open(File.json_uploaded_to_lyrics.value) as f:
        uploaded_to_lyrics = json.load(f)

    for v in uploaded_to_lyrics:
        cursor.execute("""
                INSERT INTO uploaded_to_lyrics
                VALUES (:song_id, :uploaded_id, :title, :channel_name, :channel_id, :publish_date, :video_id)
            """, {'song_id': v['original'], 'uploaded_id': v['lyrics'], 'title': v['title'],
                  'channel_name': 'ncs_arabi', 'channel_id': 'UCLbsLjqzPKBLa7kzlEmfCXA',
                  'publish_date': None, 'video_id': None})
    conn.commit()

# db = Database('ncs_arabi')
# conn = db.get_connection()
# cur = conn.cursor()
# videos = cur.execute('SELECT max(publish_date) as date FROM `uploaded_to_lyrics`').fetchone()
# print(videos)
