import re
import shutil

import requests


def get_bg_from_wallpaperflare(url):
    ext = re.search(r'/(.*)(?P<ext>\..*)', url).group('ext')
    res = requests.get(url, stream=True)
    # image_file = f"{Paths.BACKGROUNDS}{filename}{ext}"
    # print(image_file)
    with open(image_file, 'wb') as out_file:
        shutil.copyfileobj(res.raw, out_file)
    return ext


def get_bg_from_reddit(url, filename):
    result = re.search(r'/(.*)(?P<ext>\..*)', url)

    request.urlretrieve(url, '%s%s%s' % (Paths.BACKGROUNDS, filename, result.group('ext')))
    return result.group('ext')


def get_bg_from_pexels(url, filename):
    id = re.search(r'(.*)-(?P<id>[0-9]+)/', url)
    url_ = 'https://www.pexels.com/photo/%s/download' % id.group('id')
    opener = request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    request.install_opener(opener)
    request.urlretrieve(url_, '%s%s%s' % (Paths.BACKGROUNDS, filename, '.jpg'))
    return '.jpg'


def get_bg_from_500px(url, filename):
    payload = {'url': url}
    payload = parse.urlencode(payload).encode()
    res = request.urlopen("https://www.500pxdownload.com/pix.php", data=payload)

    encoding = res.info().get_param('charset', 'utf8')
    html = res.read().decode(encoding)

    result = re.search(r'src=\'(?P<lien>data:image/(?P<ext>.*);base(.|\n)*)\'( )*/>', html)

    img = request.urlopen(result.group('lien'))

    with open('%s%s.%s' % (Paths.BACKGROUNDS, filename, result.group('ext')), 'wb') as f:
        f.write(img.file.read())

    return '.%s' % result.group('ext')


def main(url, filename):
    if 'i.redd.it' in url:
        return get_bg_from_reddit(url, filename)
    elif '500px' in url:
        return get_bg_from_500px(url, filename)
    elif 'pexels' in url:
        return get_bg_from_pexels(url, filename)
    elif 'wallpaperflare' in url:
        return get_bg_from_wallpaperflare(url, filename)