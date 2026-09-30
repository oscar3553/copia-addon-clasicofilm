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

def add_dir(name, action, url=''):
    link_url = f"{BASE_URL}?action={action}&url={urllib.parse.quote_plus(url)}"
    li = xbmcgui.ListItem(label=name)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=link_url, listitem=li, isFolder=True)

def run(args=None):
    params = get_params()
    action = params.get('action')
    url = params.get('url')

    if not action:
        # Menú principal restaurado
        add_dir('Últimas películas', 'latest')
        add_dir('Géneros', 'genres')
        add_dir('Buscador', 'search')
        xbmcplugin.endOfDirectory(HANDLE)

    elif action == 'latest':
        # Añadido ?max-results=500 para sortear el límite de 25 de Blogger
        feed_url = "https://www.classicofilm.com/feeds/posts/default?max-results=500" 
        posts = feed.get_posts(feed_url)

        if not posts:
            xbmcgui.Dialog().notification('Clasicofilm', 'No se pudieron cargar las películas', xbmcgui.NOTIFICATION_ERROR, 3000)
            return

        for p in posts:
            li = xbmcgui.ListItem(label=p['title'])
            if p['thumb']:
                li.setArt({'thumb': p['thumb'], 'icon': p['thumb']})
            
            link_url = f"{BASE_URL}?action=play&url={urllib.parse.quote_plus(p['url'])}"
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=link_url, listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(HANDLE)

    elif action == 'play' and url:
        servers = parser.extract(url)
        
        if not servers:
            xbmcgui.Dialog().ok('Clasicofilm Error', 'No se encontró ningún enlace de OK.ru en el código de esta página web.')
            return

        ok_embed_url = servers[0][1]
        stream_url = parser.resolve(ok_embed_url)

        if stream_url:
            play_item = xbmcgui.ListItem(path=stream_url)
            xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        else:
            xbmcgui.Dialog().ok('Clasicofilm Error', 'El enlace de OK.ru se encontró, pero Kodi no pudo extraer el video directo.')
            
    elif action in ['genres', 'search']:
        xbmcgui.Dialog().ok('Clasicofilm', 'Sección en construcción para adaptarla a Blogger.')
