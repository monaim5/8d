import json
import re
import subprocess
import time
from shutil import copyfile

from models import Song, Song8d, AEP, Video, UploadedVideo, Channel
from paths import Other, Binary, File
from pywinauto import Application
from pywinauto.timings import wait_until_passes
from pywinauto.findwindows import ElementNotFoundError
from youtube_upload.main import main as yt_main


def create_8d_song(song: Song) -> Song8d:
    song8d = Song8d(song)
    copyfile(song.path, Other.flp_song.value)
    time.perf_counter()
    app = Application(backend="uia").start(f'"{Binary.fl_studio.value}" "{song8d.flp_path}"')
    try:
        fl = wait_until_passes(timeout=10,
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


def create_aep(song_8d: Song8d):
    payload = {
        'duration': float(song_8d.song.duration),
        'origin_song': song_8d.song.path.__str__(),
        'song_8d': song_8d.path.__str__(),
        'bg': 'path ot bg',
        'color': 'color'
    }

    with open(File.json_bridge.value, 'w') as f:
        json.dump(payload, f, sort_keys=True, indent=2)

    subprocess.call([Binary.afterfx_com.value, '-r', File.to_8d_script.value])

    return True


def render_aep(aep: AEP) -> Video:
    video = Video(aep)
    if video.exists():
        return video
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
    publish_date = channel.next_publish_date()

    for arg in kwargs:
        arguments.append(f'--{arg.replace("_", "-")}={kwargs.get(arg)}')
    arguments.extend((f'--client-secrets={channel.client_secrets}',
                      f'--credentials-file={channel.yt_credentials}',
                      f'--publish-at={publish_date}'))
    arguments.append(video.path)

    uploaded_video.published_date = publish_date
    video_ids = yt_main(arguments)
    uploaded_video.yt_video_id = video_ids[0]

    return uploaded_video
