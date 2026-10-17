import re, urllib.request, urllib.parse, html, xbmc, json

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[Clasicofilm Parser] {msg}", level)

def fetch(url, referer='https://flyf.lat/'):
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

# ============================================================
# EXTRACTOR GENERAL
# ============================================================

def extract(post_url):
    html_content = fetch(post_url)
    if not html_content:
        return []

    sources = []

    # Flyfile
    flyfile_matches = re.findall(r'(https?://(?:flyf\.lat|flyfile\.[a-z]+)/embed/[a-zA-Z0-9_\-]+)', html_content)
    for fly_url in set(flyfile_matches):
        sources.append(('Flyfile', fly_url))

    # Dzen.ru / Yandex
    dzen_matches = re.findall(r'(dzen\.ru/embed/[a-zA-Z0-9_\-]+|zen\.yandex\.ru/embed/[a-zA-Z0-9_\-]+)', html_content)
    for dzen_url in set(dzen_matches):
        clean_url = dzen_url if dzen_url.startswith('http') else f"https://{dzen_url}"
        sources.append(('Dzen.ru', clean_url))

    log(f"Fuentes detectadas: {len(sources)}")
    return sources

# ============================================================
# ROUTER DE RESOLVER
# ============================================================

def resolve(embed_url):
    log(f"Resolviendo servidor para: {embed_url}")

    if 'flyf.lat' in embed_url or 'flyfile' in embed_url:
        return resolve_flyfile(embed_url)

    elif 'dzen.ru' in embed_url or 'zen.yandex' in embed_url:
        return resolve_dzen(embed_url)

    log(f"Servidor no soportado: {embed_url}", xbmc.LOGWARNING)
    return None, None

# ============================================================
# RESOLVER FLYFILE (Multi-endpoint API & CDN Fallback)
# ============================================================

def resolve_flyfile(embed_url):
    try:
        if not embed_url.startswith('http'):
            embed_url = f"https://{embed_url}"

        video_id = embed_url.rstrip('/').split('/')[-1]
        log(f"Flyfile: Procesando video_id: {video_id}")

        stream_url = None
        
        # Lista de posibles endpoints de API según su estructura de rutas
        api_targets = [
            f"https://api.flyfile.app/api/public/media/{video_id}",
            f"https://api.flyfile.app/api/public/embed/{video_id}",
            f"https://api.flyfile.app/v1/media/{video_id}",
            f"https://api.flyfile.app/v1/embed/{video_id}",
            f"https://api.flyfile.app/api/media/{video_id}"
        ]

        # 1. Intentos vía API con cabeceras completas
        for target in api_targets:
            try:
                req = urllib.request.Request(target, headers={
                    'User-Agent': UA,
                    'Origin': 'https://flyf.lat',
                    'Referer': embed_url,
                    'Accept': 'application/json, text/plain, */*'
                })
                res_bytes = urllib.request.urlopen(req, timeout=5).read()
                res_text = res_bytes.decode('utf-8', 'ignore')
                
                # Si responde un JSON, escaneamos la respuesta
                if res_text.startswith('{') or res_text.startswith('['):
                    data = json.loads(res_text)
                    # Búsqueda en estructuras JSON comunes
                    if isinstance(data, dict):
                        stream_url = data.get('file') or data.get('url') or data.get('stream') or data.get('src')
                        if not stream_url and 'data' in data and isinstance(data['data'], dict):
                            stream_url = data['data'].get('file') or data['data'].get('url') or data['data'].get('stream')
                
                if stream_url:
                    log(f"Flyfile: Encontrado vía API ({target}): {stream_url}")
                    break
            except Exception as e:
                continue

        # 2. Fallback direct al servidor CDN (omg10.com u otros servidores de entrega)
        if not stream_url:
            log("Flyfile: API no devolvió enlace directo, probando extracción CDN...")
            html_content = fetch(embed_url, referer='https://flyf.lat/')
            
            # Buscar patrones tipo https://omg10.com/4/... o master.m3u8
            match = re.search(r'["\']((?:https?:)?//(?:omg\d+\.[a-z]+|[^\s"\'<>]+)/(?:4/\d+|master\.m3u8|[^\s"\'<>]+\.(?:m3u8|mp4)))["\']', html_content)
            if match:
                stream_url = match.group(1)
                log(f"Flyfile: Encontrado vía CDN Regex: {stream_url}")

        if stream_url:
            if stream_url.startswith('//'):
                stream_url = f"https:{stream_url}"

            # Cabeceras requeridas para la reproducción HLS en Kodi Android
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://flyf.lat/')}&Origin={urllib.parse.quote('https://flyf.lat')}"
            stream_type = 'hls' if '.m3u8' in stream_url or '/4/' in stream_url else 'mp4'
            
            log(f"Flyfile resuelto exitosamente ({stream_type}): {stream_url}")
            return stream_url + headers, stream_type

        log("Flyfile: No se pudo resolver el enlace por ninguna vía", xbmc.LOGERROR)

    except Exception as e:
        log(f"Error resolviendo Flyfile: {str(e)}", xbmc.LOGERROR)

    return None, None

# ============================================================
# RESOLVER DZEN.RU
# ============================================================

def resolve_dzen(embed_url):
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
