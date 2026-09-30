import re, urllib.request, urllib.parse, json, html, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://ok.ru/'
        })
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
        html_content = fetch(embed_url)
        if not html_content:
            return None

        # 1. Intentar extraer desde data-options
        raw_json = None
        match = re.search(r'data-options="([^"]+)"', html_content) or re.search(r"data-options='([^']+)'", html_content)
        if match:
            raw_json = html.unescape(match.group(1))

        videos = []

        if raw_json:
            try:
                options = json.loads(raw_json)
                videos_str = options.get('flashvars', {}).get('metadata', '')
                if videos_str:
                    metadata = json.loads(videos_str)
                    videos = metadata.get('videos', [])
            except Exception:
                pass

        # 2. Si no se encontró en data-options, buscar directamente "videos":[...] en el HTML
        if not videos:
            match_videos = re.search(r'"videos"\s*:\s*(\[[^\]]+\])', html_content)
            if match_videos:
                try:
                    videos = json.loads(match_videos.group(1))
                except Exception:
                    pass

        if not videos:
            xbmc.log(f"[Clasicofilm] No se encontraron vídeos en el JSON de {embed_url}", xbmc.LOGERROR)
            return None

        # Prioridad de resoluciones
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
            # Desescapar caracteres unicode o barras en la URL si existen
            stream_url = html.unescape(stream_url).replace('\\/', '/')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://ok.ru/')}"
            return stream_url + headers

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error resolviendo OK.ru ({embed_url}): {str(e)}", xbmc.LOGERROR)

    return None
