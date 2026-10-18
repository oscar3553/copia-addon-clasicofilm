import re
import json
import urllib.request
import xbmc

UA = {'User-Agent': 'Mozilla/5.0'}

def log(msg, level=xbmc.LOGINFO):
    xbmc.log("[Clasicofilm] " + str(msg), level)

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception as e:
        log("FETCH ERROR: %s" % e, xbmc.LOGERROR)
        return ""

# -------------------------------------------------
# EXTRACT
# -------------------------------------------------

def extract(post_url):

    h = fetch(post_url)

    out = []

    # DZEN
    dzen = re.findall(
        r'https://dzen\.ru/embed/[^"\'>\s]+',
        h
    )

    for x in set(dzen):
        out.append(('Dzen', x))

    # FLYFILE
    fly = re.findall(
        r'https://flyf\.lat/embed/[^"\'>\s]+',
        h
    )

    for x in set(fly):
        out.append(('FlyFile', x))

    log("Fuentes encontradas: %s" % out)

    return out

# -------------------------------------------------
# DZEN
# -------------------------------------------------

def resolve_dzen(url):

    h = fetch(url)

    m = re.search(
        r'"url":"(http[^"]+?\.m3u8[^"]*?)"',
        h
    )

    if m:
        return m.group(1).replace('\\\\', '').replace('\\', '')

    return None

# -------------------------------------------------
# FLYFILE TEST
# -------------------------------------------------

def resolve_flyfile(embed_url):

    try:

        video_id = embed_url.rstrip('/').split('/')[-1]

        log("FLYFILE VIDEO ID = %s" % video_id)

        api_url = (
            "https://api.flyfile.app/api/public/file/%s"
            % video_id
        )

        data = fetch(api_url)

        log("FLYFILE FILE API:")
        log(data[:3000])

        assign_url = (
            "https://api.flyfile.app/api/streaming/assign/%s"
            % video_id
        )

        assign = fetch(assign_url)

        log("FLYFILE ASSIGN API:")
        log(assign)

        try:
            j = json.loads(assign)

            host = j.get("url")
            token = j.get("token")

            log("HOST = %s" % host)
            log("TOKEN = %s" % token)

        except Exception as e:
            log("JSON ERROR: %s" % e)

        return None

    except Exception as e:

        log("FLYFILE ERROR: %s" % e, xbmc.LOGERROR)

    return None
