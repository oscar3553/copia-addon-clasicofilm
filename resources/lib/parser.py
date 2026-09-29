import re, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except:
        return ""

def extract(post_url):
    h = fetch(post_url)
    
    # Busca URLs de embed de VK completas dentro del HTML
    pattern = r'https://(?:vk\.com|vkvideo\.ru)/video_ext\.php\?[^"\'\>\s<]+'
    
    vk_urls = set(re.findall(pattern, h))
    
    # Devolvemos los enlaces encontrados
    return [('VK', x.replace('&amp;', '&')) for x in vk_urls]
