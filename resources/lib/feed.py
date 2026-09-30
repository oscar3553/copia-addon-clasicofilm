import urllib.request, xml.etree.ElementTree as ET, xbmc, xbmcgui

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def get_posts(feed_url):
    """
    Obtiene las entradas del blog desde el Feed RSS/Atom de Blogger.
    """
    try:
        req = urllib.request.Request(feed_url, headers={
            'User-Agent': UA,
            'Accept': 'application/atom+xml,application/xml,text/xml'
        })
        
        response = urllib.request.urlopen(req, timeout=15)
        xml_data = response.read()

        if not xml_data:
            xbmcgui.Dialog().ok('Clasicofilm Diagnostic', 'El RSS de Blogger devolvió una respuesta vacía.')
            return []

        root = ET.fromstring(xml_data)
        items = []

        # Blogger usa espacios de nombres Atom (http://www.w3.org/2005/Atom)
        # 1. Intentar parsear formato Atom (predeterminado en Blogger)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns) or root.findall('.//{http://www.w3.org/2005/Atom}entry')

        if entries:
            for entry in entries:
                title_elem = entry.find('atom:title', ns) or entry.find('{http://www.w3.org/2005/Atom}title')
                title = title_elem.text if title_elem is not None and title_elem.text else 'Sin título'

                # Buscar el enlace de la entrada (rel="alternate")
                link = ''
                links = entry.findall('atom:link', ns) or entry.findall('{http://www.w3.org/2005/Atom}link')
                for l in links:
                    if l.attrib.get('rel') == 'alternate' or 'rel' not in l.attrib:
                        link = l.attrib.get('href', '')
                        break

                # Buscar miniatura (media:thumbnail)
                thumb = ''
                media_thumb = entry.find('.//{http://search.yahoo.com/mrss/}thumbnail')
                if media_thumb is not None:
                    thumb = media_thumb.attrib.get('url', '')

                if link:
                    items.append({'title': title, 'url': link, 'thumb': thumb})

        # 2. Si no es Atom, probar el formato RSS tradicional (RSS 2.0)
        else:
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                title = title_elem.text if title_elem is not None and title_elem.text else 'Sin título'
                link = link_elem.text if link_elem is not None and link_elem.text else ''
                
                if link:
                    items.append({'title': title, 'url': link, 'thumb': ''})

        if not items:
            xbmcgui.Dialog().ok('Clasicofilm Diagnostic', f'Se descargó el feed pero no se leyeron entradas.\nTamaño devuelto: {len(xml_data)} bytes.')

        return items

    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error leyendo feed Blogger: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok('Clasicofilm Error', f'Error leyendo el Feed de Blogger:\n{str(e)}')
        return []
