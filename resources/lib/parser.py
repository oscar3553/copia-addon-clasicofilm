import re, urllib.request, urllib.parse, json, html, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://ok.ru/'})
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error en fetch: {str(e)}", xbmc.LOGERROR)
        return ""

def extract(post_url):
    html_content = fetch(post_url)
    # Expresión regular mejorada para detectar enlaces //ok.ru o http://ok.ru o https://ok.ru
    pattern = r'(?:https?:)?//(?:www\.)?ok\.ru/(?:videoembed|video)/(\d+)'
    matches = re.findall(pattern, html_content)
    links = list(set(matches))
    return [('OK.ru', f"https://ok.ru/videoembed/{m}") for m in links]

def resolve(embed_url):
    try:
        html_content = fetch(embed_url)
        if not html_content:
            return None

        match = re.search(r'data-options="([^"]+)"', html_content)
        if not match:
            return None

        raw_json = html.unescape(match.group(1))
        options = json.loads(raw_json)

        videos_str = options.get('flashvars', {}).get('metadata', '')
        if not videos_str:
            return None

        metadata = json.loads(videos_str)
        videos = metadata.get('videos', [])

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
            headers = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote('https://ok.ru/')}"
            return stream_url + headers

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error resolviendo OK.ru: {str(e)}", xbmc.LOGERROR)

    return None
