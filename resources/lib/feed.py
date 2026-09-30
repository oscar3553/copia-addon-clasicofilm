import urllib.request, xml.etree.ElementTree as ET, xbmc

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def get_posts(feed_url):
    """
    Obtiene la lista de artículos/películas desde el Feed RSS de WordPress.
    """
    try:
        req = urllib.request.Request(feed_url, headers={'User-Agent': UA})
        xml_data = urllib.request.urlopen(req, timeout=15).read()
        root = ET.fromstring(xml_data)
        
        items = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else 'Sin título'
            link = item.find('link').text if item.find('link') is not None else ''
            
            # Buscar imagen/thumbnail si está disponible en la etiqueta media
            thumb = ''
            enclosure = item.find('enclosure')
            if enclosure is not None and 'image' in enclosure.attrib.get('type', ''):
                thumb = enclosure.attrib.get('url', '')

            if link:
                items.append({
                    'title': title,
                    'url': link,
                    'thumb': thumb
                })
        return items
    except Exception as e:
        xbmc.log(f"[Clasicofilm] Error leyendo feed RSS ({feed_url}): {str(e)}", xbmc.LOGERROR)
        return []
