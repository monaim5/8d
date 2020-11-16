import json
import re
import subprocess
import time
from shutil import copyfile

from models import Song, Song8d, AEP, Video
from paths import Dir, Other, Binary, File
from pywinauto import Application
from pywinauto.timings import wait_until_passes
from pywinauto.findwindows import ElementNotFoundError


def create_8d_song(song: Song) -> Song8d:
    song8d = Song8d(song)
    print('------------------creating 8d song-------------------------')
    time.sleep(5)
    print('song converted to 8d after 5s')
    return song8d
    copyfile(song.path, Other.flp_song.value)
    time.perf_counter()
    app = Application(backend="uia").start(f'"{Binary.fl_studio.value}" "{song8d.flp_path}"')
    try:
        fl = wait_until_passes(timeout=10,
                               retry_interval=0.1,
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
    print('------------------creating aep-------------------------')
    time.sleep(5)
    print('aep created after 5s')
    return True
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
    print('------------------render_aep-------------------------')
    time.sleep(5)
    print('aep rendered after 5s')
    return video
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


def upload_video():
    print('------------------upload video-------------------------')
    time.sleep(5)
    print('video uploaded 8d after 5s')
