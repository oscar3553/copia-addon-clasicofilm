import re, urllib.request, urllib.parse

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

    # Busca enlaces de FlyF (los guardamos bajo la misma etiqueta para que el addon los procese)
    for x in set(re.findall(r'https://flyf\.lat/v/[^"\'\>\s]+', h)):
        enlaces.append(('Dzen', x))

    return enlaces

def resolve_dzen(url):
    # SI EL ENLACE ES DE FLYF
    if 'flyf.lat' in url or 'flyfile' in url:
        h = fetch(url, referer="https://flyf.lat")
        m = re.search(r'(https://[^"\']+\.m3u8[^"\']*)', h)
        if m:
            url_m3u8 = m.group(1).replace('\\\\', '').replace('\\', '')

            # Formateamos las cabeceras HTTP necesarias para activar Inputstream.Adaptive en Kodi
            ua_enc = urllib.parse.quote(UA['User-Agent'])
            ref_enc = urllib.parse.quote("https://flyf.lat")

            parametros_kodi = (
                f"|User-Agent={ua_enc}&Referer={ref_enc}"
                f"&@inputstream=inputstream.adaptive"
                f"&@inputstream.adaptive.manifest_type=hls"
                f"&@inputstream.adaptive.manifest_headers=User-Agent%3D{ua_enc}%26Referer%3D{ref_enc}"
            )
            return f"{url_m3u8}{parametros_kodi}"
        return None

    # SI EL ENLACE ES DE DZEN (Tu lógica original intacta)
    h = fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m: 
        return m.group(1).replace('\\\\', '').replace('\\', '')
    return None
