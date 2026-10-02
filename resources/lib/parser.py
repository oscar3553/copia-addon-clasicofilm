import re, urllib.request, urllib.parse, json, html, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch(url, referer='https://my.mail.ru/'):
    """Realiza peticiones HTTP emulando un navegador"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': referer
        })
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error consultando URL ({url}): {str(e)}", xbmc.LOGERROR)
        return ""

def extract(post_url):
    """Detecta automáticamente enlaces de Mail.ru o Dzen.ru en el post de Blogger"""
    html_content = fetch(post_url)
    if not html_content:
        return []

    sources = []

    # 1. Buscar Mail.ru (my.mail.ru/video/embed/ID)
    mailru_matches = re.findall(r'my\.mail\.ru/(?:video/embed/|.+/video/.+/)\b(\d+)\b', html_content)
    for vid_id in set(mailru_matches):
        sources.append(('Mail.ru', f"https://my.mail.ru/video/embed/{vid_id}"))

    # 2. Buscar Dzen.ru / Yandex Zen
    dzen_matches = re.findall(r'(dzen\.ru/embed/[a-zA-Z0-9_\-]+|zen\.yandex\.ru/embed/[a-zA-Z0-9_\-]+)', html_content)
    for dzen_url in set(dzen_matches):
        clean_url = dzen_url if dzen_url.startswith('http') else f"https://{dzen_url}"
        sources.append(('Dzen.ru', clean_url))

    return sources

def resolve(embed_url):
    """Resuelve la URL directa según el servidor detectado"""
    if 'mail.ru' in embed_url:
        return resolve_mailru(embed_url)
    elif 'dzen.ru' in embed_url or 'zen.yandex' in embed_url:
        return resolve_dzen(embed_url)
    
    xbmc.log(f"[Clasicofilm] Servidor no compatible: {embed_url}", xbmc.LOGWARNING)
    return None

def resolve_mailru(embed_url):
    """Extracción nativa para Mail.ru"""
    try:
        match_id = re.search(r'(\d{15,25})', embed_url)
        if not match_id:
            return None
            
        video_id = match_id.group(1)
        meta_url = f"https://my.mail.ru/+/video/meta/{video_id}"
        meta_json_str = fetch(meta_url, referer=f"https://my.mail.ru/video/embed/{video_id}")
        
        if not meta_json_str:
            return None

        meta_data = json.loads(meta_json_str)
        videos = meta_data.get('videos', [])
        if not videos:
            return None

        stream_url = None
        for quality in ['1080p', '720p', '480p', '360p']:
            for v in videos:
                if str(v.get('key')) == quality and v.get('url'):
                    stream_url = v.get('url')
                    break
            if stream_url:
                break

        if not stream_url and videos:
            stream_url = videos[-1].get('url') or videos[0].get('url')

        if stream_url:
            if stream_url.startswith("//"):
                stream_url = "https:" + stream_url
            stream_url = html.unescape(stream_url)
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://my.mail.ru/')}"
            return stream_url + headers

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error en Mail.ru: {str(e)}", xbmc.LOGERROR)

    return None

def resolve_dzen(embed_url):
    """Extracción para Dzen.ru (versión nativa/estándar)"""
    try:
        html_content = fetch(embed_url, referer='https://dzen.ru/')
        if not html_content:
            return None

        # Búsqueda de manifest HLS / M3U8 o fuente MP4
        stream_match = re.search(r'["\'](https?://[^\s"\']+\.(?:m3u8|mp4)[^\s"\']*)["\']', html_content)
        if stream_match:
            stream_url = html.unescape(stream_match.group(1)).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://dzen.ru/')}"
            return stream_url + headers

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error en Dzen.ru: {str(e)}", xbmc.LOGERROR)

    return None
