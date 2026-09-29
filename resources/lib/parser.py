import re, urllib.request, urllib.parse, xbmc

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
    
    # Busca cualquier coincidencia de video_ext.php de VK
    pattern = r'https?://(?:www\.)?(?:vk\.com|vkvideo\.ru)/video_ext\.php\?[^"\'\>\s<]+'
    vk_urls = list(set(re.findall(pattern, h)))
    
    xbmc.log(f"[Clasicofilm] URLs de VK encontradas en el post: {vk_urls}", xbmc.LOGINFO)
    
    return [('VK', x.replace('&amp;', '&')) for x in vk_urls]

def resolve_vk(embed_url):
    """
    Descarga el HTML del embed de VK y extrae la URL directa con cabeceras de reproducción para Kodi.
    """
    html = fetch(embed_url)
    stream_url = None
    
    # 1. Buscar enlace HLS/m3u8
    m3u8_match = re.search(r'"hls"\s*:\s*"([^"]+)"', html)
    if m3u8_match:
        stream_url = m3u8_match.group(1).replace('\\/', '/')

    # 2. Si no hay HLS, buscar calidades MP4
    if not stream_url:
        for quality in ['url1080', 'url720', 'url480', 'url360']:
            mp4_match = re.search(rf'"{quality}"\s*:\s*"([^"]+)"', html)
            if mp4_match:
                stream_url = mp4_match.group(1).replace('\\/', '/')
                break

    # 3. Expresión de respaldo para cualquier mp4/m3u8
    if not stream_url:
        generic = re.search(r'https?://[^\s"\'\\]+?\.(?:m3u8|mp4)[^\s"\'\\]*', html)
        if generic:
            stream_url = generic.group(0).replace('\\/', '/')

    if stream_url:
        # Añadimos las cabeceras HTTP que necesita el reproductor de Kodi para no ser rechazado por VK
        headers_str = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://vkvideo.ru/')}"
        final_play_url = stream_url + headers_str
        xbmc.log(f"[Clasicofilm] Stream resuelto con éxito: {final_play_url}", xbmc.LOGINFO)
        return final_play_url

    xbmc.log(f"[Clasicofilm] No se pudo resolver la URL del embed: {embed_url}", xbmc.LOGERROR)
    return None
