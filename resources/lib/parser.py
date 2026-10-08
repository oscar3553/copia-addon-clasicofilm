import re, urllib.request, urllib.parse, html, xbmc, json

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

    # Archive.org
    archive_matches = re.findall(r'(archive\.org/embed/[a-zA-Z0-9_\-]+)', html_content)
    for archive_url in set(archive_matches):
        clean_url = archive_url if archive_url.startswith('http') else f"https://{archive_url}"
        sources.append(('Archive.org', clean_url))

    # Dzen.ru
    dzen_matches = re.findall(r'(dzen\.ru/embed/[a-zA-Z0-9_\-]+|zen\.yandex\.ru/embed/[a-zA-Z0-9_\-]+)', html_content)
    for dzen_url in set(dzen_matches):
        clean_url = dzen_url if dzen_url.startswith('http') else f"https://{dzen_url}"
        sources.append(('Dzen.ru', clean_url))

    # VK clásico
    vk_matches = re.findall(r'(https?://(?:vk\.com|vk\.ru)/video[-]?\d+_\d+)', html_content)
    for vk_url in set(vk_matches):
        sources.append(('VK', vk_url))

    # VK video_ext.php
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
    """
    Scraping del reproductor móvil de VK (Android compatible).
    """
    try:
        # Extraer owner_id y video_id
        m = re.search(r'/video(-?\d+)_(\d+)', embed_url)
        if m:
            owner_id, video_id = m.group(1), m.group(2)
        else:
            oid = re.search(r'oid=(-?\d+)', embed_url)
            vid = re.search(r'id=(\d+)', embed_url)
            if oid and vid:
                owner_id = oid.group(1)
                video_id = vid.group(1)
            else:
                log("VK: No se pudo extraer owner_id y video_id", xbmc.LOGERROR)
                return None, None

        # Reproductor móvil (funciona en Android)
        mobile_url = f"https://m.vk.com/video?z=video{owner_id}_{video_id}"

        html_content = fetch(mobile_url, referer='https://m.vk.com/')
        if not html_content:
            log("VK: no se pudo obtener HTML móvil", xbmc.LOGERROR)
            return None, None

        # Buscar manifest HLS dentro del JSON del reproductor móvil
        hls_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html_content)
        if hls_match:
            stream_url = hls_match.group(1).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://m.vk.com/')}"
            log(f"VK móvil HLS encontrado: {stream_url}")
            return stream_url + headers, 'hls'

        # Fallback: MP4
        mp4_match = re.search(r'"url"\s*:\s*"([^"]+\.mp4[^"]*)"', html_content)
        if mp4_match:
            stream_url = mp4_match.group(1).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://m.vk.com/')}"
            log(f"VK móvil MP4 encontrado: {stream_url}")
            return stream_url + headers, 'mp4'

        log("VK: no se encontró stream en reproductor móvil", xbmc.LOGERROR)
        return None, None

    except Exception as e:
        log(f"Error resolviendo VK móvil: {str(e)}", xbmc.LOGERROR)
        return None, None
