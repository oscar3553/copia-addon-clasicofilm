import json, urllib.request, urllib.parse, re
BASE='https://www.classicofilm.com'
UA={'User-Agent':'Mozilla/5.0'}

def get(url):
    req=urllib.request.Request(url,headers=UA)
    return json.loads(urllib.request.urlopen(req,timeout=20).read().decode())

def clean_html(text):
    text = re.sub(r'&nbsp;|&#8230;|&quot;|&ndash;', ' ', text)
    text = re.sub(r'<[^>]*>', ' ', text)
    return ' '.join(text.split())

def extract_meta(html):
    director = ""; reparto = ""; clean_text = clean_html(html)
    m_dir = re.search(r'Director:?\s*([^.]+)', clean_text, re.I)
    if m_dir: director = m_dir.group(1).strip()
    m_rep = re.search(r'Reparto:?\s*([^.]+)', clean_text, re.I)
    if m_rep: reparto = m_rep.group(1).strip()
    plot = clean_text
    for m in ['Director:', 'Reparto:', 'Título original:', 'Año:', 'Género:', 'País:']:
        idx = plot.find(m)
        if idx != -1: plot = plot[:idx]
    return re.sub(r'^Sinopsis:?\s*', '', plot, flags=re.I).strip(), director, reparto

def parse(data):
    out=[]
    entries = data.get('feed',{}).get('entry',[])
    for e in entries:
        link=''
        for l in e.get('link',[]):
            if l.get('rel')=='alternate': link=l.get('href')
        img = e.get('media$thumbnail',{}).get('url','').replace('s72-c', 's1600')
        title_raw = e['title']['$t']
        plot, director, cast = extract_meta(e.get('content', {}).get('$t', ''))
        y = re.search(r'\((\d{4})\)', title_raw)
        out.append({
            'title': title_raw.split(' - ')[0].split('(')[0].strip(),
            'url': link, 'image': img, 'plot': plot, 
            'director': director, 'cast': cast.split(','), 'year': y.group(1) if y else ""
        })
    n_url = ''
    for l in data.get('feed',{}).get('link',[]):
        if l.get('rel') == 'next': n_url = l.get('href')
    return out, n_url

def latest(url=None): return parse(get(url if url else BASE+'/feeds/posts/default?alt=json&max-results=50'))
def labels():
    try:
        d=get(BASE+'/feeds/posts/default?alt=json&max-results=50'); s=set()
        for e in d.get('feed',{}).get('entry',[]):
            for c in e.get('category',[]): s.add(c['term'])
        return sorted(s)
    except: return []
def by_label(l, url=None): return parse(get(url if url else BASE+f'/feeds/posts/default/-/{urllib.parse.quote(l)}?alt=json&max-results=50'))
def search(q): return parse(get(BASE+f'/feeds/posts/default?alt=json&q={urllib.parse.quote(q)}&max-results=50'))
