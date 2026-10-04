import re, urllib.request, urllib.parse, json, html, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[Clasicofilm Parser] {msg}", level)

def fetch(url, referer='https://rumble.com/'):
    """Realiza peticiones HTTP emulando un navegador"""
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
    """Detecta automáticamente enlaces de Rumble o Dzen.ru en el post de Blogger"""
    html_content = fetch(post_url)
    if not html_content:
        return []

    sources = []

    # 1. Buscar Rumble (ejemplo: rumble.com/embed/v7e6tpq/)
    rumble_matches = re.findall(r'(rumble\.com/embed/[a-zA-Z0-9_\-]+)', html_content)
    for rumble_url in set(rumble_matches):
        clean_url = rumble_url if rumble_url.startswith('http') else f"https://{rumble_url}"
        sources.append(('Rumble', clean_url))

    # 2. Buscar Dzen.ru / Yandex Zen
    dzen_matches = re.findall(r'(dzen\.ru/embed/[a-zA-Z0-9_\-]+|zen\.yandex\.ru/embed/[a-zA-Z0-9_\-]+)', html_content)
    for dzen_url in set(dzen_matches):
        clean_url = dzen_url if dzen_url.startswith('http') else f"https://{dzen_url}"
        sources.append(('Dzen.ru', clean_url))

    log(f"Fuentes detectadas: {len(sources)}")
    return sources

def resolve(embed_url):
    """Resuelve la URL directa de reproducción según el servidor"""
    log(f"Resolviendo: {embed_url}")
    if 'rumble.com' in embed_url:
        return resolve_rumble(embed_url)
    elif 'dzen.ru' in embed_url or 'zen.yandex' in embed_url:
        return resolve_dzen(embed_url)
    
    log(f"Servidor no soportado: {embed_url}", xbmc.LOGWARNING)
    return None, None

def resolve_rumble(embed_url):
    """Extrae la URL de streaming (.m3u8 o .mp4) desde el embed de Rumble"""
    try:
        html_content = fetch(embed_url, referer='https://rumble.com/')
        if not html_content:
            return None, None

        # 1. Buscar enlace HLS (.m3u8) en la respuesta del embed
        m3u8_match = re.search(r'["\'](https?://[^\s"\']+\.m3u8[^\s"\']*)["\']', html_content)
        if m3u8_match:
            stream_url = html.unescape(m3u8_match.group(1)).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://rumble.com/')}"
            return stream_url + headers, 'hls'

        # 2. Fallback: Buscar enlace directo .mp4
        mp4_match = re.search(r'["\'](https?://[^\s"\']+\.mp4[^\s"\']*)["\']', html_content)
        if mp4_match:
            stream_url = html.unescape(mp4_match.group(1)).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://rumble.com/')}"
            return stream_url + headers, 'mp4'

    except Exception as e:
        log(f"Error en Rumble: {str(e)}", xbmc.LOGERROR)

    return None, None

def resolve_dzen(embed_url):
    """Extrae el manifiesto .m3u8 o .mp4 de Dzen.ru"""
    try:
        html_content = fetch(embed_url, referer='https://dzen.ru/')
        if not html_content:
            return None, None

        stream_match = re.search(r'["\'](https?://[^\s"\']+\.(?:m3u8|mp4)[^\s"\']*)["\']', html_content)
        if stream_match:
            stream_url = html.unescape(stream_match.group(1)).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://dzen.ru/')}"
            stream_type = 'hls' if '.m3u8' in stream_url else 'mp4'
            return stream_url + headers, stream_type

    except Exception as e:
        log(f"Error en Dzen.ru: {str(e)}", xbmc.LOGERROR)

    return None, None
