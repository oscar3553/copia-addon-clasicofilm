import re, urllib.request, urllib.parse, xbmc, json

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': UA,
                'Referer': 'https://vkvideo.ru/'
            }
        )
        return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error en fetch ({url}): {str(e)}", xbmc.LOGERROR)
        return ""

def extract(post_url):
    h = fetch(post_url)
    pattern = r'https?://(?:www\.)?(?:vk\.com|vkvideo\.ru)/video_ext\.php\?[^"\'\>\s<]+'
    vk_urls = list(set(re.findall(pattern, h)))
    return [('VK', x.replace('&amp;', '&')) for x in vk_urls]

def resolve_vk(embed_url):
    """
    Descarga la página del embed de VK y extrae los enlaces directos (.mp4 o .m3u8)
    descodificando las variables JavaScript de VK.
    """
    html = fetch(embed_url)
    stream_url = None

    # 1. Buscar en el JSON interno de VK (al_video / player options)
    # Reemplazamos secuencias escapadas unicode y slashes
    clean_html = html.replace('\\/', '/').replace('\\"', '"')
    
    # Buscar patrones HLS / m3u8
    hls_matches = re.findall(r'https?://[^\s"\'\\]+?\.(?:m3u8)[^\s"\'\\]*', clean_html)
    if hls_matches:
        stream_url = hls_matches[0]

    # 2. Si no hay HLS, buscar enlaces MP4 directos (url1080, url720, url480, url360, etc.)
    if not stream_url:
        for res in ['1080', '720', '480', '360', '240']:
            pattern = rf'"url{res}"\s*:\s*"([^"]+)"'
            match = re.search(pattern, clean_html)
            if match:
                stream_url = match.group(1)
                break

    # 3. Expresión regular de respaldo para cualquier MP4 directo
    if not stream_url:
        mp4_matches = re.findall(r'https?://[^\s"\'\\]+?\.(?:mp4)[^\s"\'\\]*', clean_html)
        if mp4_matches:
            stream_url = mp4_matches[0]

    if stream_url:
        # Formatear adecuadamente y adjuntar cabeceras requeridas por Kodi
        stream_url = urllib.parse.unquote(stream_url).replace('&amp;', '&')
        headers_str = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://vkvideo.ru/')}"
        final_play_url = stream_url + headers_str
        xbmc.log(f"[Clasicofilm] Stream resuelto con éxito: {final_play_url}", xbmc.LOGINFO)
        return final_play_url

    xbmc.log(f"[Clasicofilm] No se pudo resolver la URL del embed: {embed_url}", xbmc.LOGERROR)
    return None
