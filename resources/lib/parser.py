import re, urllib.request, urllib.parse, html, xbmc, json

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[Clasicofilm Parser] {msg}", level)

def fetch(url, referer='https://archive.org/'):
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

def extract(post_url):
    html_content = fetch(post_url)
    if not html_content:
        return []

    sources = []

    # 1. Archive.org
    archive_matches = re.findall(r'(archive\.org/embed/[a-zA-Z0-9_\-]+)', html_content)
    for archive_url in set(archive_matches):
        clean_url = archive_url if archive_url.startswith('http') else f"https://{archive_url}"
        sources.append(('Archive.org', clean_url))

    # 2. Dzen.ru / Yandex
    dzen_matches = re.findall(r'(dzen\.ru/embed/[a-zA-Z0-9_\-]+|zen\.yandex\.ru/embed/[a-zA-Z0-9_\-]+)', html_content)
    for dzen_url in set(dzen_matches):
        clean_url = dzen_url if dzen_url.startswith('http') else f"https://{dzen_url}"
        sources.append(('Dzen.ru', clean_url))

    # 3. VK.com / VK.ru formato clásico
    vk_matches = re.findall(r'(https?://(?:vk\.com|vk\.ru)/video[-]?\d+_\d+)', html_content)
    for vk_url in set(vk_matches):
        sources.append(('VK', vk_url))

    # 4. VK video_ext.php (vkvideo.ru o vk.com)
    vk_ext_matches = re.findall(r'(https?://(?:vkvideo\.ru|vk\.com)/video_ext\.php\?[^"\']+)', html_content)
    for vk_url
