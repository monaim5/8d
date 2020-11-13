import re
import time
from shutil import copyfile

from func_timeout import func_timeout, FunctionTimedOut

from config import Config
from models import Song, Song8d
from paths import Dir, Other, Binary
from pywinauto import Application
from pywinauto.timings import wait_until_passes
from pywinauto.findwindows import ElementNotFoundError


def create_8d_song(song: Song) -> Song8d:
    song8d = Song8d(song)
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
