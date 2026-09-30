import re, urllib.request, urllib.parse, json, html, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://ok.ru/'})
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error en fetch: {str(e)}", xbmc.LOGERROR)
        return ""

def extract(post_url):
    """Extrae IDs e incrustaciones de OK.ru del HTML del post"""
    html_content = fetch(post_url)
    if not html_content:
        return []

    # Extrae el ID numérico único sin importar si trae http, https, // o parámetros como ?nochat=1
    pattern = r'ok\.ru/(?:videoembed|video)/(\d+)'
    matches = re.findall(pattern, html_content)
    
    # Eliminar duplicados
    video_ids = list(set(matches))
    
    # Retornar las URLs de incrustación limpias y estandarizadas
    return [('OK.ru', f"https://ok.ru/videoembed/{vid_id}") for vid_id in video_ids]

def resolve(embed_url):
    """Obtiene la URL directa .mp4 con máxima calidad de OK.ru"""
    try:
        html_content = fetch(embed_url)
        if not html_content:
            return None

        # Buscar los datos de configuración en el atributo data-options
        match = re.search(r'data-options="([^"]+)"', html_content)
        if not match:
            return None

        raw_json = html.unescape(match.group(1))
        options = json.loads(raw_json)

        videos_str = options.get('flashvars', {}).get('metadata', '')
        if not videos_str:
            return None

        metadata = json.loads(videos_str)
        videos = metadata.get('videos', [])

        # Prioridad de resoluciones de mayor a menor calidad
        quality_order = ['full', 'hd', 'standard', 'low', 'lowest', 'mobile']
        stream_url = None

        for q in quality_order:
            for v in videos:
                if v.get('name') == q:
                    stream_url = v.get('url')
                    break
            if stream_url:
                break

        if not stream_url and videos:
            stream_url = videos[0].get('url')

        if stream_url:
            # Adjuntar las cabeceras HTTP necesarias para evitar el error 403 en Kodi
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://ok.ru/')}"
            return stream_url + headers

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error resolviendo OK.ru ({embed_url}): {str(e)}", xbmc.LOGERROR)

    return None
