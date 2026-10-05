import re, urllib.request, urllib.parse, html, xbmc, json

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[Clasicofilm Parser] {msg}", level)

def fetch(url, referer='https://archive.org/'):
    """Realiza peticiones HTTP limpias con User-Agent estándar"""
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
    """Detecta enlaces de Archive.org o Dzen.ru en la entrada de Blogger"""
    html_content = fetch(post_url)
    if not html_content:
        return []

    sources = []

    # 1. Detección de Archive.org (embed o ID)
    archive_matches = re.findall(r'(archive\.org/embed/[a-zA-Z0-9_\-]+)', html_content)
    for archive_url in set(archive_matches):
        clean_url = archive_url if archive_url.startswith('http') else f"https://{archive_url}"
        sources.append(('Archive.org', clean_url))

    # 2. Detección de Dzen.ru / Yandex
    dzen_matches = re.findall(r'(dzen\.ru/embed/[a-zA-Z0-9_\-]+|zen\.yandex\.ru/embed/[a-zA-Z0-9_\-]+)', html_content)
    for dzen_url in set(dzen_matches):
        clean_url = dzen_url if dzen_url.startswith('http') else f"https://{dzen_url}"
        sources.append(('Dzen.ru', clean_url))

    log(f"Fuentes detectadas: {len(sources)}")
    return sources

def resolve(embed_url):
    """Enruta al resolvedor correspondiente"""
    log(f"Resolviendo servidor para: {embed_url}")
    if 'archive.org' in embed_url:
        return resolve_archive(embed_url)
    elif 'dzen.ru' in embed_url or 'zen.yandex' in embed_url:
        return resolve_dzen(embed_url)
    
    log(f"Servidor no soportado: {embed_url}", xbmc.LOGWARNING)
    return None, None

def resolve_archive(embed_url):
    """Extrae la URL MP4 directa de Archive.org"""
    try:
        # Extraer el ID del item (ej. 012_20261004)
        item_id = embed_url.split('/embed/')[-1].split('/')[0].split('?')[0]
        if item_id:
            meta_url = f"https://archive.org/metadata/{item_id}"
            json_str = fetch(meta_url, referer='https://archive.org/')
            if json_str:
                data = json.loads(json_str)
                server = data.get('server', 'ia800000.us.archive.org')
                dir_path = data.get('dir', '')
                
                # Buscar el archivo .mp4 dentro del elemento
                for f in data.get('files', []):
                    if f.get('name', '').lower().endswith('.mp4'):
                        file_name = f['name']
                        stream_url = f"https://{server}{dir_path}/{file_name}"
                        headers = f"|User-Agent={urllib.parse.quote(UA)}"
                        log(f"Archive.org MP4 resuelto: {stream_url}")
                        return stream_url + headers, 'mp4'

        # Fallback: Escaneo directo por Regex en el HTML del embed
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
    """Extrae el stream HLS (.m3u8) o MP4 de Dzen.ru"""
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
