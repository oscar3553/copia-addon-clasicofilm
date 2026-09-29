import re, urllib.request, urllib.parse, xbmc, json, html

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
    return [('VK', html.unescape(x).replace('&amp;', '&')) for x in vk_urls]

def resolve_vk(embed_url):
    """
    Extrae la URL reproducible analizando los objetos JSON internos y bloques de configuración de VK.
    """
    raw_html = fetch(embed_url)
    if not raw_html:
        return None

    # Normalización del contenido
    cleaned = html.unescape(raw_html).replace('\\/', '/').replace('\\"', '"')
    stream_url = None

    # 1. Búsqueda directa de manifiesto HLS/m3u8 en cualquier parte del HTML/JSON
    hls_matches = re.findall(r'https?://[^\s"\'\\]+?\.(?:m3u8)[^\s"\'\\]*', cleaned)
    if hls_matches:
        stream_url = hls_matches[0]

    # 2. Búsqueda dentro de bloques JSON de payload/files
    if not stream_url:
        # Extraer posibles URLs de fuentes mp4 etiquetadas por calidad
        for q in ['1080', '720', '480', '360', '240']:
            match = re.search(rf'"url{q}"\s*:\s*"([^"]+)"', cleaned)
            if match:
                stream_url = match.group(1)
                break

    # 3. Búsqueda por parámetros "files" de VK (ej: "mp4_720", "hls", "failover_host")
    if not stream_url:
        match_files = re.search(r'"files"\s*:\s*(\{.+?\})', cleaned)
        if match_files:
            try:
                files_json = json.loads(match_files.group(1))
                stream_url = files_json.get('hls') or files_json.get('mp4_720') or files_json.get('mp4_1080') or files_json.get('mp4_480')
            except Exception:
                pass

    # 4. Coincidencia genérica para cualquier archivo MP4 válido de CDN
    if not stream_url:
        mp4_generic = re.findall(r'https?://[^\s"\'\\]+?\.(?:mp4)[^\s"\'\\]*', cleaned)
        if mp4_generic:
            stream_url = mp4_generic[0]

    if stream_url:
        # Decodificación final de caracteres Unicode y construcción de cabeceras para Kodi
        stream_url = urllib.parse.unquote(stream_url).replace('&amp;', '&')
        
        # Eliminar posibles residuos de comillas o comas al final
        stream_url = stream_url.rstrip('",;')
        
        headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://vkvideo.ru/')}"
        final_url = stream_url + headers
        xbmc.log(f"[Clasicofilm] Stream VK resuelto con éxito: {final_url}", xbmc.LOGINFO)
        return final_url

    xbmc.log(f"[Clasicofilm] No se pudo extraer enlace de vídeo del embed: {embed_url}", xbmc.LOGERROR)
    return None
