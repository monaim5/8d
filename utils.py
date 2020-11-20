import json
import re
import subprocess
import time
from datetime import datetime
from random import random
from shutil import copyfile

from config import Bcolors, Color
from models import Song, Song8d, AEP, Video, UploadedVideo, Channel, Background
from paths import Other, Binary, File
from pywinauto import Application
from pywinauto.timings import wait_until_passes
from pywinauto.findwindows import ElementNotFoundError
from youtube_upload.main import main as yt_main


def create_8d_song(song: Song) -> Song8d:
    song8d = Song8d(song)
    if song8d.exists():
       return song8d
    copyfile(song.path, Other.flp_song.value)
    time.perf_counter()
    app = Application(backend="uia").start(f'"{Binary.fl_studio.value}" "{song8d.flp_path}"')
    try:
        fl = wait_until_passes(timeout=120,
                               retry_interval=2,
                               func=lambda: app.top_window().children()[0])

        fl.type_keys('^+r')
        save_as = wait_until_passes(timeout=10,
                                    retry_interval=0.1,
                                    func=lambda: app.top_window().child_window(title='Save As'))

        file_name = save_as.child_window(title="File name:",
                                         auto_id="FileNameControlHost",
                                         control_type="ComboBox")

        file_name = file_name.child_window(title="File name:",
                                           auto_id="1001",
                                           class_name='Edit')

        save = save_as.child_window(title="Save", auto_id="1", control_type="Button")

        file_name.set_text(song8d.title)
        # file_name.type_keys(' ', with_spaces=True)
        save_as.type_keys('{VK_F4}')
        save_as.type_keys('^a')
        save_as.type_keys(song8d.path.parent, with_spaces=True)
        save_as.type_keys('{ENTER}')
        save.click()
        renderer = wait_until_passes(timeout=10,
                                     retry_interval=0.1,
                                     func=lambda: app.top_window().
                                     child_window(title_re="Rendering to .*", control_type="Pane", found_index=1))

        renderer.type_keys('{ENTER}')

        renderer = Application().connect(title_re='Rendering: .*').window(title_re='Rendering: .*')
        print("\nRendering start")
        while True:
            try:
                progress = re.findall('\d+/\d+', renderer.texts()[0])
                print(progress[0])
                time.sleep(1)
            except ElementNotFoundError:
                print("\nrendering completed")
                break
        return song8d
    finally:
        app.kill()


def create_aep(song_8d: Song8d, background: Background, color: Color):
    aep = AEP(song_8d, background, color)
    payload = {
        'duration': float(song_8d.song.duration),
        'original_song': song_8d.song.path.__str__(),
        'song_8d': song_8d.path.__str__(),
        'aep': aep.path.__str__(),
        'template': aep.template_path.__str__(),
        'bg': background.path.__str__(),
        'color': color.value
    }

    with open(File.json_bridge.value, 'w') as f:
        json.dump(payload, f, sort_keys=True, indent=2)

    subprocess.call([Binary.afterfx_com.value, '-r', File.to_8d_script.value])

    return aep


def render_aep(aep: AEP) -> Video:
    video = Video(aep)
    if video.exists():
        return aep.video
    subprocess.call(
        [Binary.aerender.value,
         '-project', aep.path,
         '-OMtemplate', 'H.264',
         '-comp', 'Comp',
         '-output', f'"{video.path}"'
         ])

    return video


def upload_video(video: Video, channel: Channel, **kwargs) -> UploadedVideo:
    # edited the youtube_upload.main.run_main and youtube_upload.main.main
    # by adding (video_ids: list) for return it at the end, by the main function

    uploaded_video = UploadedVideo(video, channel)

    arguments = []

    for arg in kwargs:
        arguments.append(f'--{arg.replace("_", "-")}={kwargs.get(arg)}')
    arguments.extend((f'--client-secrets={channel.client_secrets}',
                      f'--credentials-file={channel.yt_credentials}',
                      f'--category={channel.category}'))
    arguments.append(video.path.__str__())

    uploaded_video.published_date = kwargs['publish_at'] if kwargs['publish_at'] is not None else datetime.now()

    upload_try = 1
    while upload_try <= 3:
        try:
            print(f'{Bcolors.WARNING.value}{Bcolors.BOLD.value}the {upload_try} try{Bcolors.ENDC.value}')
            uploaded_video.yt_video_id = yt_main(arguments)[0]
            return uploaded_video

        except ConnectionResetError as e:
            upload_try += 1
            print(f'try {upload_try} {e.__class__} : {e}')

    raise ConnectionResetError

