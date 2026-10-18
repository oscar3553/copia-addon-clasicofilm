import re, urllib.request
UA={'User-Agent':'Mozilla/5.0'}
def fetch(url):
    try:
        req=urllib.request.Request(url,headers=UA)
        return urllib.request.urlopen(req,timeout=20).read().decode('utf-8','ignore')
    except: return ""
def extract(post_url):
    h=fetch(post_url)
    return [('Dzen', x) for x in set(re.findall(r'https://dzen\.ru/embed/[^"\'\>\s]+', h))]
def resolve_dzen(url):
    h=fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m: return m.group(1).replace('\\\\', '').replace('\\', '')
    return None
