import sys, urllib.parse, xbmc, xbmcgui, xbmcplugin
from resources.lib import feed, parser

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL = sys.argv[0] if len(sys.argv) > 0 else ''

def get_params():
    params = {}
    if len(sys.argv) > 2 and sys.argv[2]:
        cleaned_args = sys.argv[2].lstrip('?')
        params = dict(urllib.parse.parse_qsl(cleaned_args))
    return params

def run():
    params = get_params()
    action = params.get('action')
    url = params.get('url')

    if not action:
        # Menú principal: Cargar lista de películas desde tu web
        # Cambia esta URL por la dirección RSS de tu WordPress si es distinta
        feed_url = "https://classicofilm.com/feed/" 
        posts = feed.get_posts(feed_url)

        for p in posts:
            li = xbmcgui.ListItem(label=p['title'])
            if p['thumb']:
                li.setArt({'thumb': p['thumb'], 'icon': p['thumb']})
            
            # Construir URL interna para seleccionar la película
            link_url = f"{BASE_URL}?action=play&url={urllib.parse.quote_plus(p['url'])}"
            
            # Marcar el elemento como reproducible
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=link_url, listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(HANDLE)

    elif action == 'play' and url:
        # 1. Buscar enlace de OK.ru en el post de WordPress
        servers = parser.extract(url)
        
        if not servers:
            xbmcgui.Dialog().notification('Clasicofilm', 'No se encontró enlace de OK.ru', xbmcgui.NOTIFICATION_ERROR, 3000)
            return

        # Tomar el primer servidor OK.ru encontrado
        ok_embed_url = servers[0][1]

        # 2. Extraer el enlace directo .mp4 de OK.ru
        stream_url = parser.resolve(ok_embed_url)

        if stream_url:
            play_item = xbmcgui.ListItem(path=stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().notification('Clasicofilm', 'Error resolviendo el vídeo de OK.ru', xbmcgui.NOTIFICATION_ERROR, 3000)
