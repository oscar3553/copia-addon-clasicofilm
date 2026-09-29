import re, urllib.request

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
    except:
        return ""

def extract(post_url):
    h = fetch(post_url)
    
    # Busca la URL del iframe de VK dentro del post de WordPress
    pattern = r'https://(?:vk\.com|vkvideo\.ru)/video_ext\.php\?[^"\'\>\s<]+'
    vk_urls = set(re.findall(pattern, h))
    
    return [('VK', x.replace('&amp;', '&')) for x in vk_urls]

def resolve_vk(embed_url):
    """
    Descarga el HTML del embed de VK y extrae la URL directa del video (m3u8 o mp4)
    """
    html = fetch(embed_url)
    
    # 1. Buscar enlace HLS/m3u8
    m3u8_match = re.search(r'"hls"\s*:\s*"([^"]+)"', html)
    if m3u8_match:
        return m3u8_match.group(1).replace('\\/', '/')

    # 2. Buscar URLs directas MP4 por resolución (de mayor a menor)
    for quality in ['url1080', 'url720', 'url480', 'url360']:
        mp4_match = re.search(rf'"{quality}"\s*:\s*"([^"]+)"', html)
        if mp4_match:
            return mp4_match.group(1).replace('\\/', '/')
            
    # 3. Expresión regular de respaldo para mp4 / m3u8
    generic = re.search(r'https?://[^\s"\'\\]+?\.(?:m3u8|mp4)[^\s"\'\\]*', html)
    if generic:
        return generic.group(0).replace('\\/', '/')
        
    return None
