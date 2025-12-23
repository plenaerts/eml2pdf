"""Security related html sanitization."""

from bs4 import BeautifulSoup


def sanitize_html(html_content):
    """Remove potential privacy and security issues from HTML content.

    Sanitizes HTML by removing or neutralizing dangerous elements and attributes
    before PDF generation. This provides defense-in-depth protection against
    various attack vectors.

    Protected Against:
        - Script execution (script, iframe, object, embed tags)
        - Data exfiltration via forms
        - Privacy leaks via remote resources (tracking pixels, web beacons)
        - Cross-Site Scripting via event handlers (onclick, onload, onerror, etc.)
        - Remote resource loading (meta redirects, external stylesheets)
        - CSS-based tracking via url() references
        - External link navigation

    Processing Steps:
        1. Removes risky HTML tags (script, iframe, object, embed, video, audio,
           form, meta, link)
        2. Removes remote images (http:// or https:// sources)
        3. Clears style attributes containing url() references
        4. Neutralizes external links by replacing href with '#'
        5. Removes event handler attributes (on*) and data attributes (data-*)

    Args:
        html_content (str): The HTML content to sanitize.

    Returns:
        str: Sanitized HTML content safe for PDF rendering.

    Note:
        Only embedded images (data URIs or CID references) are preserved.
        Remote images are completely removed to prevent tracking.

    Example:
        >>> html = '<img src="http://tracker.com/pixel.gif"><script>alert(1)</script>'
        >>> sanitize_html(html)
        ''
    """
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
