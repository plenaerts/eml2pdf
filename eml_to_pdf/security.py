"""Security related html sanitization."""

from bs4 import BeautifulSoup


def sanitize_html(html_content):
    """Remove a number of potential privacy and security issues from html."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove risky tags
    risky_tags = ['script', 'iframe', 'object', 'embed', 'video', 'audio',
                  'form', 'meta', 'link']
    for tag in soup.find_all(risky_tags):
        tag.decompose()

    # Remove remote images
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src.startswith('http://') or src.startswith('https://'):
            img.decompose()

    # Sanitize styles
    for tag in soup.find_all(style=True):
        if 'url(' in tag['style']:
            tag['style'] = ''

    # Sanitize links
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if href.startswith(('http://', 'https://')):
            a['href'] = '#'

    # Remove event handlers and custom data attributes
    for tag in soup.find_all():
        for attr in list(tag.attrs):
            if attr.startswith('on') or attr.startswith('data-'):
                del tag[attr]

    return str(soup)
