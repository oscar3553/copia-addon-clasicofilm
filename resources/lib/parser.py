import re, urllib.request, urllib.parse, json, html, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch(url, data=None):
    headers = {
        'User-Agent': UA,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Referer': 'https://ok.ru/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error en fetch ({url}): {str(e)}", xbmc.LOGERROR)
        return ""

def extract(post_url):
    """Extrae IDs e incrustaciones de OK.ru del HTML del post"""
    html_content = fetch(post_url)
    if not html_content:
        return []

    pattern = r'ok\.ru/(?:videoembed|video)/(\d+)'
    matches = re.findall(pattern, html_content)
    video_ids = list(set(matches))
    return [('OK.ru', f"https://ok.ru/videoembed/{vid_id}") for vid_id in video_ids]

def resolve(embed_url):
    """Obtiene la URL directa .mp4 con máxima calidad de OK.ru"""
    try:
        video_id_match = re.search(r'(\d+)', embed_url)
        if not video_id_match:
            return None
        vid_id = video_id_match.group(1)

        videos = []

        # 1. Consultar la API de metadatos vía POST (Simula la petición nativa del reproductor)
        api_url = f"https://ok.ru/dk?cmd=videoPlayerMetadata&vid={vid_id}"
        post_data = urllib.parse.urlencode({'post': 'true'}).encode('utf-8')
        response_data = fetch(api_url, data=post_data)

        if response_data:
            try:
                data_json = json.loads(response_data)
                videos = data_json.get('videos', [])
            except Exception:
                pass

        # 2. Si la respuesta contiene 'metadata' escapado dentro del JSON
        if not videos and response_data:
            try:
                meta_match = re.search(r'"metadata"\s*:\s*"([^"]+)"', response_data)
                if meta_match:
                    meta_str = html.unescape(meta_match.group(1)).replace('\\"', '"').replace('\\/', '/')
                    meta_json = json.loads(meta_str)
                    videos = meta_json.get('videos', [])
            except Exception:
                pass

        # 3. Búsqueda directa con Expresión Regular de URLs de vídeo directo si falla el JSON
        if not videos and response_data:
            urls = re.findall(r'"url"\s*:\s*"([^"]+)"', response_data)
            if urls:
                clean_urls = [html.unescape(u).replace('\\/', '/') for u in urls if 'st.cmd' not in u]
                if clean_urls:
                    stream_url = clean_urls[0]
                    headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://ok.ru/')}"
                    return stream_url + headers

        if not videos:
            xbmc.log(f"[Clasicofilm] No se encontraron listas de vídeo para ID: {vid_id}", xbmc.LOGERROR)
            return None

        # Ordenar selecciones de mayor a menor resolución
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
            stream_url = html.unescape(stream_url).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://ok.ru/')}"
            return stream_url + headers

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error resolviendo OK.ru ({embed_url}): {str(e)}", xbmc.LOGERROR)

    return None
