import re
import urllib.request
import urllib.parse
import json

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

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
    
    for x in set(re.findall(r'https://dzen\.ru/embed/[^"\'\>\s]+', h)):
        enlaces.append(('Dzen', x))
        
    fly_matches = set(re.findall(r'https://flyf\.lat/(?:embed|v)/[^"\'\>\s]+', h))
    for x in fly_matches:
        enlaces.append(('Dzen', x))
        
    return enlaces

def resolve_dzen(url):
    if isinstance(url, list):
        if len(url) > 0:
            url = url[0]
        else:
            return None

    if 'flyf.lat' in url or 'flyfile' in url:
        video_id = url.rstrip('/').split('/')[-1]
        
        # 1. Intentar consultar la API oficial de Flyfile si el ID es válido
        api_urls = [
            f"https://api.flyfile.app/api/public/video/{video_id}",
            f"https://api.flyfile.app/api/public/embed/{video_id}"
        ]
        
        stream_url = None
        for api_url in api_urls:
            try:
                req = urllib.request.Request(api_url, headers={**UA, 'Origin': 'https://flyf.lat', 'Referer': url})
                res = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', 'ignore')
                if res.startswith('{'):
                    data = json.loads(res)
                    stream_url = data.get('file') or data.get('url') or data.get('stream') or data.get('src')
                    if not stream_url and 'data' in data and isinstance(data['data'], dict):
                        stream_url = data['data'].get('file') or data['data'].get('url')
                    if stream_url:
                        break
            except:
                continue

        # 2. Fallback por análisis de la página embed si la API no responde
        if not stream_url:
            h = fetch(url, referer="https://flyf.lat/")
            m = re.search(r'["\']((?:https?:)?//[^\s"\'<>]+(?:m3u8|streaming-[^\s"\'<>]+)[^\s"\'<>]*?)["\']', h)
            if m:
                stream_url = m.group(1).replace('\\/', '/')

        if stream_url:
            if stream_url.startswith('//'):
                stream_url = f"https:{stream_url}"
            
            ua_enc = urllib.parse.quote(UA['User-Agent'])
            ref_enc = urllib.parse.quote("https://flyf.lat/")
            
            parametros_kodi = (
                f"|User-Agent={ua_enc}&Referer={ref_enc}"
                f"&@inputstream=inputstream.adaptive"
                f"&@inputstream.adaptive.manifest_type=hls"
                f"&@inputstream.adaptive.manifest_headers=User-Agent%3D{ua_enc}%26Referer%3D{ref_enc}"
            )
            return f"{stream_url}{parametros_kodi}"
        return None

    # Dzen fallback
    h = fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m: 
        return m.group(1).replace('\\\\', '').replace('\\', '')
    return None
