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
    """Extrae IDs e incrustaciones de OK.ru del HTML del post limpiando parámetros"""
    html_content = fetch(post_url)
    if not html_content:
        return []

    pattern = r'ok\.ru/(?:videoembed|video)/(\d+)'
    matches = re.findall(pattern, html_content)
    video_ids = list(set(matches))
    return [('OK.ru', f"https://ok.ru/videoembed/{vid_id}") for vid_id in video_ids]

def resolve(embed_url):
    """Obtiene la URL directa de streaming de OK.ru con limpiador profundo de JSON y fallback"""
    try:
        # 1. Asegurar la extracción del ID numérico puro sin parámetros adicionales (?nochat=1, etc.)
        vid_match = re.search(r'(\d+)', embed_url)
        if not vid_match:
            return None
        clean_id = vid_match.group(1)
        clean_embed_url = f"https://ok.ru/videoembed/{clean_id}"

        html_content = fetch(clean_embed_url)
        if not html_content:
            return None

        # 2. Extraer el bloque data-options
        match = re.search(r'data-options="([^"]+)"', html_content) or re.search(r"data-options='([^']+)'", html_content)
        if not match:
            xbmc.log(f"[Clasicofilm] No se encontró data-options en {clean_embed_url}", xbmc.LOGERROR)
            return None

        # Decodificación limpia de entidades HTML y caracteres Unicode
        raw_options = html.unescape(match.group(1))
        options = json.loads(raw_options)

        flashvars = options.get('flashvars', {})
        videos = []

        # Extraer lista de vídeos parseando posible sub-cadena JSON
        if isinstance(flashvars, dict):
            metadata = flashvars.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            videos = metadata.get('videos', [])
        elif isinstance(flashvars, str):
            fv_json = json.loads(flashvars)
            metadata = fv_json.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            videos = metadata.get('videos', [])

        stream_url = None

        # 3. Selección de calidad por objeto JSON
        if videos:
            quality_order = ['full', 'hd', 'sd', 'standard', 'low', 'lowest', 'mobile']
            for q in quality_order:
                for v in videos:
                    if v.get('name') == q and v.get('url'):
                        stream_url = v.get('url')
                        break
                if stream_url:
                    break

            if not stream_url and videos:
                stream_url = videos[0].get('url')

        # 4. Fallback directo por regex si el parseo del JSON de metadata no devolvió lista de vídeos
        if not stream_url:
            # Busca URLs directas con firma en el texto plano de data-options
            urls_found = re.findall(r'&quot;url&quot;:&quot;(https?:\\?/\\?/[^&]+)&quot;', match.group(1))
            if urls_found:
                # Filtrar SWF o recursos estáticos
                valid_urls = [u for u in urls_found if 'st.cmd' not in u and 'MegaPlayer' not in u]
                if valid_urls:
                    stream_url = valid_urls[0]

        if not stream_url:
            xbmc.log(f"[Clasicofilm] No se pudo extraer la URL del flujo para {clean_embed_url}", xbmc.LOGERROR)
            return None

        # Sanear la URL extraída
        stream_url = html.unescape(stream_url).replace('\\/', '/').replace('\\u0026', '&')

        headers_list = [
            f"User-Agent={urllib.parse.quote(UA)}",
            f"Referer={urllib.parse.quote('https://ok.ru/')}",
            f"Origin={urllib.parse.quote('https://ok.ru')}",
            "Sec-Fetch-Dest=video",
            "Sec-Fetch-Mode=cors",
            "Sec-Fetch-Site=cross-site",
            "Connection=keep-alive"
        ]

        headers_str = "&".join(headers_list)
        return f"{stream_url}|{headers_str}"

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error resolviendo OK.ru ({embed_url}): {str(e)}", xbmc.LOGERROR)

    return None
