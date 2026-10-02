import urllib.parse, xbmcplugin, xbmcgui, xbmc
from .feed import latest,labels,by_label,search
from .parser import extract,resolve_dzen

HANDLE=None

def movie_item(m, argv):
    # Título en dorado para la lista
    label = f"[COLOR gold]{m['title']}[/COLOR]"
    if m['year']: label += f" ({m['year']})"
    li = xbmcgui.ListItem(label=label)
    
    # Metadatos completos para la ficha técnica
    li.setInfo('video', {
        'title': m['title'], 'plot': m['plot'], 'director': m['director'], 
        'cast': m['cast'], 'mediatype': 'movie', 'year': int(m['year']) if m['year'] else 0
    })
    
    # Artes con rutas locales para asegurar logo
    li.setArt({
        'thumb': m['image'], 'poster': m['image'], 
        'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png',
        'fanart': 'special://home/addons/plugin.video.clasicofilm/fanart.jpg'
    })
    
    li.setProperty('IsPlayable', 'false')
    u = f"{argv[0]}?action=info_and_play&url={urllib.parse.quote(m['url'])}"
    xbmcplugin.addDirectoryItem(HANDLE, u, li, False)

def run(argv):
    global HANDLE
    HANDLE=int(argv[1]); p=urllib.parse.parse_qs(argv[2][1:]); a=p.get('action',[''])[0]
    
    if a=='info_and_play':
        xbmc.executebuiltin('Action(Info)') # Forzamos la ficha al hacer click
        url_post = urllib.parse.unquote(p['url'][0])
        src = extract(url_post)
        dzen = [u for n,u in src if n=='Dzen']
        if dzen:
            f = resolve_dzen(dzen[0])
            if f: xbmcplugin.setResolvedUrl(HANDLE, True, xbmcgui.ListItem(path=f))
        return
        
    if a=='latest':
        items, n_url = latest(p.get('next_page', [None])[0])
        xbmcplugin.setContent(HANDLE, 'movies')
        for m in items: movie_item(m, argv)
        if n_url:
            u = f"{argv[0]}?action=latest&next_page={urllib.parse.quote(n_url)}"
            xbmcplugin.addDirectoryItem(HANDLE, u, xbmcgui.ListItem(label='[COLOR gold]➡ SIGUIENTE PÁGINA[/COLOR]'), True)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a=='genres':
        for l in labels():
            li = xbmcgui.ListItem(label=f"[COLOR gold]•[/COLOR] {l}")
            li.setArt({'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'})
            xbmcplugin.addDirectoryItem(HANDLE, f"{argv[0]}?action=genre&name={urllib.parse.quote(l)}", li, True)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a=='genre':
        name = p['name'][0]
        items, n_url = by_label(name, p.get('next_page', [None])[0])
        xbmcplugin.setContent(HANDLE, 'movies')
        for m in items: movie_item(m, argv)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a=='search':
        kb = xbmcgui.Dialog().input('Buscar película...', type=xbmcgui.INPUT_ALPHANUM)
        if kb:
            items, _ = search(kb)
            xbmcplugin.setContent(HANDLE, 'movies')
            for m in items: movie_item(m, argv)
            xbmcplugin.endOfDirectory(HANDLE)
        return

    # MENÚ PRINCIPAL (3 CARPETAS)
    menu = [('🎬 ÚLTIMAS NOVEDADES','latest'), ('🎭 GÉNEROS','genres'), ('🔍 BUSCAR','search')]
    for label, act in menu:
        li = xbmcgui.ListItem(label=label)
        li.setArt({'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'})
        xbmcplugin.addDirectoryItem(HANDLE, f"{argv[0]}?action={act}", li, True)
    xbmcplugin.endOfDirectory(HANDLE)
