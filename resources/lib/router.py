import urllib.parse, xbmcplugin, xbmcgui, xbmc
from .feed import latest, labels, by_label, search
from .parser import extract, resolve  # <--- Importamos 'resolve' genérico que soporta Mail.ru y Dzen.ru

HANDLE = None

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
    
    # Artes con rutas locales
    li.setArt({
        'thumb': m['image'], 'poster': m['image'], 
        'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png',
        'fanart': 'special://home/addons/plugin.video.clasicofilm/fanart.jpg'
    })
    
    # === CAMBIO CLAVE 1: Marcar como reproducible ===
    li.setProperty('IsPlayable', 'true')
    
    u = f"{argv[0]}?action=play&url={urllib.parse.quote(m['url'])}"
    xbmcplugin.addDirectoryItem(HANDLE, u, li, False)

def run(argv):
    global HANDLE
    HANDLE = int(argv[1]); p = urllib.parse.parse_qs(argv[2][1:]); a = p.get('action', [''])[0]
    
    # === CAMBIO CLAVE 2: Proceso de reproducción unificado (Mail.ru + Dzen.ru) ===
   if a == 'play':
        url_post = urllib.parse.unquote(p['url'][0])
        src = extract(url_post)
        
        if not src:
            xbmcgui.Dialog().notification('Clasicofilm', 'No se encontraron vídeos', xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
            return

        stream_url = None
        for server_name, embed_url in src:
            stream_url = resolve(embed_url)
            if stream_url:
                break

        if stream_url:
            play_item = xbmcgui.ListItem(path=stream_url)
            play_item.setMimeType('video/mp4')
            play_item.setContentLookup(False)
            play_item.setProperty('IsPlayable', 'true')
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().notification('Clasicofilm', 'Error al resolver el enlace', xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return
        
    if a == 'latest':
        items, n_url = latest(p.get('next_page', [None])[0])
        xbmcplugin.setContent(HANDLE, 'movies')
        for m in items: movie_item(m, argv)
        if n_url:
            u = f"{argv[0]}?action=latest&next_page={urllib.parse.quote(n_url)}"
            xbmcplugin.addDirectoryItem(HANDLE, u, xbmcgui.ListItem(label='[COLOR gold]➡ SIGUIENTE PÁGINA[/COLOR]'), True)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a == 'genres':
        for l in labels():
            li = xbmcgui.ListItem(label=f"[COLOR gold]•[/COLOR] {l}")
            li.setArt({'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'})
            xbmcplugin.addDirectoryItem(HANDLE, f"{argv[0]}?action=genre&name={urllib.parse.quote(l)}", li, True)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a == 'genre':
        name = p['name'][0]
        items, n_url = by_label(name, p.get('next_page', [None])[0])
        xbmcplugin.setContent(HANDLE, 'movies')
        for m in items: movie_item(m, argv)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a == 'search':
        kb = xbmcgui.Dialog().input('Buscar película...', type=xbmcgui.INPUT_ALPHANUM)
        if kb:
            items, _ = search(kb)
            xbmcplugin.setContent(HANDLE, 'movies')
            for m in items: movie_item(m, argv)
            xbmcplugin.endOfDirectory(HANDLE)
        return

    # MENÚ PRINCIPAL (3 CARPETAS)
    menu = [('🎬 ÚLTIMAS NOVEDADES', 'latest'), ('🎭 GÉNEROS', 'genres'), ('🔍 BUSCAR', 'search')]
    for label, act in menu:
        li = xbmcgui.ListItem(label=label)
        li.setArt({'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'})
        xbmcplugin.addDirectoryItem(HANDLE, f"{argv[0]}?action={act}", li, True)
    xbmcplugin.endOfDirectory(HANDLE)
