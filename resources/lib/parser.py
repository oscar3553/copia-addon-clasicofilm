import re, urllib.request, urllib.parse, xbmc, html

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
    Descarga el HTML del embed de VK y busca cualquier patron de video (.m3u8 o .mp4)
    aplicando unescapes completos de unicode y entidades HTML.
    """
    raw_html = fetch(embed_url)
    
    # Decodificar entidades HTML y secuencias Unicode de JavaScript (\u0026 -> &, \/ -> /)
    cleaned = html.unescape(raw_html)
    cleaned = cleaned.replace('\\/', '/').replace('\\u0026', '&')
    
    # 1. Buscar cualquier URL con extension .m3u8 en el codigo
    m3u8_list = re.findall(r'https?://[^\s"\'\\]+?\.(?:m3u8)[^\s"\'\\]*', cleaned)
    if m3u8_list:
        url = m3u8_list[0].replace('&amp;', '&')
        headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://vkvideo.ru/')}"
        return url + headers

    # 2. Buscar enlaces MP4 por calidad
    for q in ['1080', '720', '480', '360', '240']:
        mp4_match = re.search(rf'"url{q}"\s*:\s*"([^"]+)"', cleaned)
        if mp4_match:
            url = mp4_match.group(1).replace('&amp;', '&')
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://vkvideo.ru/')}"
            return url + headers

    # 3. Expresion regular global para cualquier .mp4 de VK (cache/video/etc)
    mp4_generic = re.findall(r'https?://[^\s"\'\\]+?\.(?:mp4)[^\s"\'\\]*', cleaned)
    if mp4_generic:
        url = mp4_generic[0].replace('&amp;', '&')
        headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://vkvideo.ru/')}"
        return url + headers

    xbmc.log(f"[Clasicofilm] No se extrajo video de: {embed_url}", xbmc.LOGERROR)
    return None
