import urllib.parse
import xbmcplugin
import xbmcgui
import xbmc

from .feed import latest, labels, by_label, search
from .parser import extract, resolve_dzen, resolve_flyfile

HANDLE = None


def movie_item(m, argv):

    label = f"[COLOR gold]{m['title']}[/COLOR]"

    if m['year']:
        label += f" ({m['year']})"

    li = xbmcgui.ListItem(label=label)

    li.setInfo('video', {
        'title': m['title'],
        'plot': m['plot'],
        'director': m['director'],
        'cast': m['cast'],
        'mediatype': 'movie',
        'year': int(m['year']) if m['year'] else 0
    })

    li.setArt({
        'thumb': m['image'],
        'poster': m['image'],
        'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png',
        'fanart': 'special://home/addons/plugin.video.clasicofilm/fanart.jpg'
    })

    li.setProperty('IsPlayable', 'false')

    u = (
        f"{argv[0]}?action=info_and_play&url="
        f"{urllib.parse.quote(m['url'])}"
    )

    xbmcplugin.addDirectoryItem(
        HANDLE,
        u,
        li,
        False
    )


def run(argv):

    global HANDLE

    HANDLE = int(argv[1])

    p = urllib.parse.parse_qs(argv[2][1:])

    a = p.get('action', [''])[0]

    # ==================================================
    # PLAY
    # ==================================================

    if a == 'info_and_play':

        xbmc.executebuiltin('Action(Info)')

        url_post = urllib.parse.unquote(
            p['url'][0]
        )

        src = extract(url_post)

        for server, url in src:

            # -----------------------------
            # DZEN
            # -----------------------------

            if server == 'Dzen':

                stream = resolve_dzen(url)

                if stream:

                    xbmcplugin.setResolvedUrl(
                        HANDLE,
                        True,
                        xbmcgui.ListItem(path=stream)
                    )

                    return

            # -----------------------------
            # FLYFILE TEST
            # -----------------------------

            elif server == 'FlyFile':

                resolve_flyfile(url)

                xbmcgui.Dialog().ok(
                    'FlyFile',
                    'Consulta kodi.log para ver los datos obtenidos'
                )

                return

        xbmcgui.Dialog().notification(
            'Clasicofilm',
            'No se encontraron fuentes válidas',
            xbmcgui.NOTIFICATION_ERROR,
            4000
        )

        return

    # ==================================================
    # ULTIMAS NOVEDADES
    # ==================================================

    if a == 'latest':

        items, n_url = latest(
            p.get('next_page', [None])[0]
        )

        xbmcplugin.setContent(
            HANDLE,
            'movies'
        )

        for m in items:
            movie_item(m, argv)

        if n_url:

            u = (
                f"{argv[0]}?action=latest&next_page="
                f"{urllib.parse.quote(n_url)}"
            )

            xbmcplugin.addDirectoryItem(
                HANDLE,
                u,
                xbmcgui.ListItem(
                    label='[COLOR gold]➡ SIGUIENTE PÁGINA[/COLOR]'
                ),
                True
            )

        xbmcplugin.endOfDirectory(HANDLE)

        return

    # ==================================================
    # GENEROS
    # ==================================================

    if a == 'genres':

        for l in labels():

            li = xbmcgui.ListItem(
                label=f"[COLOR gold]•[/COLOR] {l}"
            )

            li.setArt({
                'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'
            })

            xbmcplugin.addDirectoryItem(
                HANDLE,
                f"{argv[0]}?action=genre&name={urllib.parse.quote(l)}",
                li,
                True
            )

        xbmcplugin.endOfDirectory(HANDLE)

        return

    # ==================================================
    # GENERO
    # ==================================================

    if a == 'genre':

        name = p['name'][0]

        items, n_url = by_label(
            name,
            p.get('next_page', [None])[0]
        )

        xbmcplugin.setContent(
            HANDLE,
            'movies'
        )

        for m in items:
            movie_item(m, argv)

        xbmcplugin.endOfDirectory(HANDLE)

        return

    # ==================================================
    # BUSCAR
    # ==================================================

    if a == 'search':

        kb = xbmcgui.Dialog().input(
            'Buscar película...',
            type=xbmcgui.INPUT_ALPHANUM
        )

        if kb:

            items, _ = search(kb)

            xbmcplugin.setContent(
                HANDLE,
                'movies'
            )

            for m in items:
                movie_item(m, argv)

            xbmcplugin.endOfDirectory(HANDLE)

        return

    # ==================================================
    # MENU PRINCIPAL
    # ==================================================

    menu = [
        ('🎬 ÚLTIMAS NOVEDADES', 'latest'),
        ('🎭 GÉNEROS', 'genres'),
        ('🔍 BUSCAR', 'search')
    ]

    for label, act in menu:

        li = xbmcgui.ListItem(label=label)

        li.setArt({
            'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'
        })

        xbmcplugin.addDirectoryItem(
            HANDLE,
            f"{argv[0]}?action={act}",
            li,
            True
        )

    xbmcplugin.endOfDirectory(HANDLE)
