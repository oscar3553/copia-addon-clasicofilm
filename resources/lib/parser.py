import re, urllib.request, urllib.parse, html, xbmc, json
import xbmcaddon

addon = xbmcaddon.Addon()

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[Clasicofilm Parser] {msg}", level)

def fetch(url, referer='https://archive.org/'):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': referer
        })
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    except Exception as e:
        log(f"Error consultando URL ({url}): {str(e)}", xbmc.LOGERROR)
        return ""

def extract(post_url):
    html_content = fetch(post_url)
    if not html_content:
        return []

    sources = []

    # 1. Archive.org
    archive_matches = re.findall(r'(archive\.org/embed/[a-zA-Z0-9_\-]+)', html_content)
    for archive_url in set(archive_matches):
        clean_url = archive_url if archive_url.startswith('http') else f"https://{archive_url}"
        sources.append(('Archive.org', clean_url))

    # 2. Dzen.ru / Yandex
    dzen_matches = re.findall(r'(dzen\.ru/embed/[a-zA-Z0-9_\-]+|zen\.yandex\.ru/embed/[a-zA-Z0-9_\-]+)', html_content)
    for dzen_url in set(dzen_matches):
        clean_url = dzen_url if dzen_url.startswith('http') else f"https://{dzen_url}"
        sources.append(('Dzen.ru', clean_url))

    # 3. VK clásico
    vk_matches = re.findall(r'(https?://(?:vk\.com|vk\.ru)/video[-]?\d+_\d+)', html_content)
    for vk_url in set(vk_matches):
        sources.append(('VK', vk_url))

    # 4. VK video_ext.php (vkvideo.ru o vk.com)
    vk_ext_matches = re.findall(r'(https?://(?:vkvideo\.ru|vk\.com)/video_ext\.php\?[^"\']+)', html_content)
    for vk_url in set(vk_ext_matches):
        sources.append(('VK', vk_url))

    log(f"Fuentes detectadas: {len(sources)}")
    return sources

def resolve(embed_url):
    log(f"Resolviendo servidor para: {embed_url}")
    if 'archive.org' in embed_url:
        return resolve_archive(embed_url)
    elif 'dzen.ru' in embed_url or 'zen.yandex' in embed_url:
        return resolve_dzen(embed_url)
    elif 'vk.com' in embed_url or 'vk.ru' in embed_url or 'vkvideo.ru' in embed_url:
        return resolve_vk(embed_url)

    log(f"Servidor no soportado: {embed_url}", xbmc.LOGWARNING)
    return None, None

def resolve_archive(embed_url):
    try:
        item_id = embed_url.split('/embed/')[-1].split('/')[0].split('?')[0]
        if item_id:
            meta_url = f"https://archive.org/metadata/{item_id}"
            json_str = fetch(meta_url, referer='https://archive.org/')
            if json_str:
                data = json.loads(json_str)
                server = data.get('server', 'ia800000.us.archive.org')
                dir_path = data.get('dir', '')
                for f in data.get('files', []):
                    if f.get('name', '').lower().endswith('.mp4'):
                        file_name = f['name']
                        stream_url = f"https://{server}{dir_path}/{file_name}"
                        headers = f"|User-Agent={urllib.parse.quote(UA)}"
                        log(f"Archive.org MP4 resuelto: {stream_url}")
                        return stream_url + headers, 'mp4'

        html_content = fetch(embed_url, referer='https://archive.org/')
        mp4_matches = re.findall(r'["\'](https?://[^\s"\']+\.mp4[^\s"\']*)["\']', html_content)
        if mp4_matches:
            stream_url = html.unescape(mp4_matches[0]).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}"
            return stream_url + headers, 'mp4'

    except Exception as e:
        log(f"Error resolviendo Archive.org: {str(e)}", xbmc.LOGERROR)

    return None, None

def resolve_dzen(embed_url):
    try:
        html_content = fetch(embed_url, referer='https://dzen.ru/')
        if not html_content:
            return None, None

        stream_match = re.search(r'["\'](https?://[^\s"\']+\.(?:m3u8|mp4)[^\s"\']*)["\']', html_content)
        if stream_match:
            stream_url = html.unescape(stream_match.group(1)).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://dzen.ru/')}"
            stream_type = 'hls' if '.m3u8' in stream_url else 'mp4'
            log(f"Dzen.ru resuelto ({stream_type}): {stream_url}")
            return stream_url + headers, stream_type

    except Exception as e:
        log(f"Error resolviendo Dzen.ru: {str(e)}", xbmc.LOGERROR)

    return None, None

def resolve_vk(embed_url):
    try:
        # 1. Formato clásico: /video-12345_67890
        m = re.search(r'/video(-?\d+)_(\d+)', embed_url)
        if m:
            owner_id, video_id = m.group(1), m.group(2)
        else:
            # 2. Formato video_ext.php?oid=-12345&id=67890
            oid = re.search(r'oid=(-?\d+)', embed_url)
            vid = re.search(r'id=(\d+)', embed_url)

            if oid and vid:
                owner_id = oid.group(1)
                video_id = vid.group(1)
            else:
                log("VK: No se pudo extraer owner_id y video_id", xbmc.LOGERROR)
                return None, None

        # Leer token desde settings
        token = addon.getSetting("vk_token")

        api_url = (
            "https://api.vk.com/method/video.get?"
            f"videos={owner_id}_{video_id}&access_token={token}&v=5.131"
        )

        log(f"Llamando API VK: {api_url}")

        req = urllib.request.Request(api_url, headers={'User-Agent': UA})
        data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))

        files = data["response"]["items"][0]["files"]

        stream_url = (
            files.get("hls") or
            files.get("mp4_1080") or
            files.get("mp4_720") or
            files.get("mp4_480") or
            files.get("mp4_360") or
            files.get("mp4_240")
        )

        if not stream_url:
            log("VK: No hay streams disponibles", xbmc.LOGERROR)
            return None, None

        headers = f"|User-Agent={urllib.parse.quote(UA)}"
        stream_type = 'hls' if '.m3u8' in stream_url else 'mp4'

        log(f"VK resuelto: {stream_url}")
        return stream_url + headers, stream_type

    except Exception as e:
        log(f"Error resolviendo VK: {str(e)}", xbmc.LOGERROR)
        return None, None
