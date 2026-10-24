import re
import urllib.request
import urllib.parse

# Usamos el User-Agent compatible con Web Video Caster / WebView para saltar bloqueos
UA = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Chromecast) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36 WVCNow/1.0'}

def fetch(url, referer=None):
    try:
        headers = UA.copy()
        if referer:
            headers['Referer'] = referer
        req = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except: 
        return ""

def extract(post_url):
    h = fetch(post_url)
    enlaces = []

    # Busca enlaces de Dzen
    for x in set(re.findall(r'https://dzen\.ru/embed/[^"\'\>\s]+', h)):
        enlaces.append(('Dzen', x))

    # Busca enlaces de FlyF (Ampliamos la búsqueda para /embed/ y /v/)
    fly_matches = set(re.findall(r'https://flyf\.lat/(?:embed|v)/[^"\'\>\s]+', h))
    for x in fly_matches:
        enlaces.append(('Dzen', x))

    return enlaces

def resolve_dzen(url):
    # Corrección: Extraemos la URL si viene en formato de lista (por seguridad del main.py)
    if isinstance(url, list):
        if len(url) > 0:
            url = url[0]
        else:
            return None

    # SI EL ENLACE DETECTADO ES DE FLYF
    if 'flyf.lat' in url or 'flyfile' in url:
        h = fetch(url, referer="https://flyf.lat")

        # Búsqueda más flexible de m3u8 o enlaces CDN en el HTML de Flyfile
        m = re.search(r'["\']((?:https?:)?//[^\s"\'<>]+(?:m3u8|mp4|4/\d+)[^\s"\'<>]*?)["\']', h)
        if not m:
            # Fallback a búsqueda simple de m3u8
            m = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', h)

        if m:
            stream_url = m.group(1).replace('\\/', '/')
            if stream_url.startswith('//'):
                stream_url = f"https:{stream_url}"

            # Formateamos las cabeceras HTTP necesarias para activar Inputstream.Adaptive en Kodi
            ua_enc = urllib.parse.quote(UA['User-Agent'])
            ref_enc = urllib.parse.quote("https://flyf.lat")

            parametros_kodi = (
                f"|User-Agent={ua_enc}&Referer={ref_enc}"
                f"&@inputstream=inputstream.adaptive"
                f"&@inputstream.adaptive.manifest_type=hls"
                f"&@inputstream.adaptive.manifest_headers=User-Agent%3D{ua_enc}%26Referer%3D{ref_enc}"
            )
            return f"{stream_url}{parametros_kodi}"
        return None

    # SI EL ENLACE ES DE DZEN (Tu lógica original intacta)
    h = fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m: 
        return m.group(1).replace('\\\\', '').replace('\\', '')
    return None
