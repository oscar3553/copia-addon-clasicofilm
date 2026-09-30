import re, urllib.request, urllib.parse, json, html, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://ok.ru/'})
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error en fetch OK.ru: {str(e)}", xbmc.LOGERROR)
        return ""

def extract_okru(post_url):
    """
    Busca URLs de OK.ru dentro del post de WordPress (formatos ok.ru/video/ ID u ok.ru/videoembed/ ID)
    """
    html_content = fetch(post_url)
    pattern = r'https?://(?:www\.)?ok\.ru/(?:videoembed|video)/(\d+)'
    matches = re.findall(pattern, html_content)
    
    # Devuelve una lista de tuplas con el servidor y la URL normalizada en formato embed
    links = list(set(matches))
    return [('OK.ru', f"https://ok.ru/videoembed/{m}") for m in links]

def resolve_okru(embed_url):
    """
    Extrae el enlace directo .mp4 de OK.ru priorizando la máxima calidad disponible (1080p -> 720p -> etc.)
    y adjuntando las cabeceras HTTP necesarias para evitar el error 403 Forbidden en Kodi.
    """
    try:
        html_content = fetch(embed_url)
        if not html_content:
            return None

        # Buscar la etiqueta data-options que contiene la información técnica del reproductor
        match = re.search(r'data-options="([^"]+)"', html_content)
        if not match:
            xbmc.log(f"[Clasicofilm] No se encontró data-options en: {embed_url}", xbmc.LOGERROR)
            return None

        # Decodificar entidades HTML y convertir a diccionario JSON
        raw_json = html.unescape(match.group(1))
        options = json.loads(raw_json)

        # Extraer el string de metadatos de los vídeos
        videos_str = options.get('flashvars', {}).get('metadata', '')
        if not videos_str:
            return None

        metadata = json.loads(videos_str)
        videos = metadata.get('videos', [])

        # Orden de prioridad de máxima a mínima calidad
        quality_order = ['full', 'hd', 'standard', 'low', 'lowest', 'mobile']
        stream_url = None

        for q in quality_order:
            for v in videos:
                if v.get('name') == q:
                    stream_url = v.get('url')
                    break
            if stream_url:
                break

        # Si no coincide con los nombres estándar, tomar el primer enlace disponible
        if not stream_url and videos:
            stream_url = videos[0].get('url')

        if stream_url:
            # Construcción de la URL con las cabeceras requeridas (User-Agent y Referer)
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://ok.ru/')}"
            final_play_url = stream_url + headers
            
            xbmc.log(f"[Clasicofilm] OK.ru resuelto con éxito: {final_play_url}", xbmc.LOGINFO)
            return final_play_url

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Excepción al resolver OK.ru: {str(e)}", xbmc.LOGERROR)

    return None
