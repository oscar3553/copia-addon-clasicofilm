import re, urllib.request
UA={'User-Agent':'Mozilla/5.0'}

def fetch(url):
    try:
        req=urllib.request.Request(url,headers=UA)
        return urllib.request.urlopen(req,timeout=20).read().decode('utf-8','ignore')
    except: return ""

def extract(post_url):
    h=fetch(post_url)
    sources = []
    
    # 1. Tu extractor clásico para Dzen.ru (se mantiene idéntico)
    dzen_links = set(re.findall(r'https://dzen\.ru/embed/[^"\'\>\s]+', h))
    for x in dzen_links:
        sources.append(('Dzen', x))
        
    # 2. NUEVO: Extractor inteligente para Hugging Face
    # Captura tanto si pones el enlace en un iframe como si usas la etiqueta <video> en Blogger
    hf_links = set(re.findall(r'https://huggingface\.co/datasets/[^"\'\>\s]+/resolve/main/[^"\'\>\s]+', h))
    for x in hf_links:
        sources.append(('HuggingFace', x))
        
    return sources

def resolve_dzen(url):
    h=fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m: return m.group(1).replace('\\\\', '').replace('\\', '')
    return None
