# resources/lib/vkresolver.py
import sys
import json
import urllib.parse
import urllib.request

import xbmcgui
import xbmcplugin

API_URL = "https://api.vk.com/method/video.get"
API_VERSION = "5.131"

def resolve_vk(owner_id, video_id, token):
    # Construir parámetros de la petición
    params = {
        "videos": f"{owner_id}_{video_id}",
        "access_token": token,
        "v": API_VERSION
    }

    url = API_URL + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        xbmcgui.Dialog().notification("VK", f"Error al conectar: {e}", xbmcgui.NOTIFICATION_ERROR)
        return

    try:
        files = data["response"]["items"][0]["files"]
    except Exception:
        xbmcgui.Dialog().notification("VK", "No se pudo obtener el vídeo (sin campo files)", xbmcgui.NOTIFICATION_ERROR)
        return

    # Prioridad de reproducción
    stream_url = (
        files.get("hls") or
        files.get("mp4_1080") or
        files.get("mp4_720") or
        files.get("mp4_480") or
        files.get("mp4_360") or
        files.get("mp4_240")
    )

    if not stream_url:
        xbmcgui.Dialog().notification("VK", "No hay streams disponibles", xbmcgui.NOTIFICATION_ERROR)
        return

    li = xbmcgui.ListItem(path=stream_url)
    li.setProperty("IsPlayable", "true")

    handle = int(sys.argv[1])
    xbmcplugin.setResolvedUrl(handle, True, li)

