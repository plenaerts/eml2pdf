# Security Features

## Overview

eml2pdf includes security features to protect users from potentially malicious
content embedded in email messages. These features are implemented in
`eml2pdf/security.py` and are enabled by default during PDF generation.

## HTML Sanitization

The primary security mechanism is the `sanitize_html()` function in
eml2pdf/security.py, which removes or neutralizes potentially dangerous
HTML elements and attributes before PDF generation.

### Protected Against

#### 1. Script Execution and Active Content

The sanitizer removes tags that can execute code or load external active content:

- `<script>` - JavaScript execution
- `<iframe>` - Embedded frames that can load external content
- `<object>` - Embedded objects (Flash, Java applets, etc.)
- `<embed>` - Alternative embedding mechanism
- `<video>` - Video elements with potential codec vulnerabilities
- `<audio>` - Audio elements with potential codec vulnerabilities

#### 2. Data Exfiltration via Forms

Forms can be used to send data to external servers:

- `<form>` - Form elements that could submit data

#### 3. Privacy Leaks via Remote Resources

Remote resources can be used to track email opens and gather information:

##### Remote Images

- Images with `src` attributes starting with `http://` or `https://` are removed
- This prevents tracking pixels and web beacons
- Only embedded images (using data URIs or CID references) are allowed

##### CSS URL References

- Inline `style` attributes containing `url()` functions are cleared
- Prevents loading of remote stylesheets, fonts, or background images

##### External Links

- Links with `href` attributes starting with `http://` or `https://` are
  replaced with `#`
- Prevents clickable links that could lead to malicious sites
- Note: This doesn't remove the link text, just neutralizes the destination

#### 4. Cross-Site Scripting (XSS) Vectors

Event handlers and data attributes can be exploited for XSS attacks:

##### Event Handlers

- All attributes starting with `on` are removed (e.g., `onclick`, `onload`, `onerror`)
- Prevents JavaScript execution via event handlers

##### Data Attributes

- All attributes starting with `data-` are removed
- Prevents storage of potentially malicious data for later exploitation

#### 5. Metadata and Resource Loading

Additional tags that can affect page behavior or load external resources:

- `<meta>` - Meta tags that could redirect or refresh
- `<link>` - Linked resources like stylesheets, icons, or prefetch hints

## Usage

### Default (Secure) Mode

By default, all HTML content is sanitized before PDF generation:

```python
from eml2pdf import libeml2pdf

# Sanitization is enabled by default (unsafe=False)
libeml2pdf.process_eml(eml_path, output_dir)
```

**Command-line**:
```bash
python -m eml2pdf input/ output/
```

### Unsafe Mode

The `--unsafe` flag disables HTML sanitization. This mode should only be used when:

- You completely trust the source of the EML files
- You understand the security risks involved

**Warning again**: Unsafe mode may expose sensitive user information through
tracking pixels, external resources, and other privacy-invasive techniques.
Consider running eml2pdf airgapped if you have reason to.

```bash
python -m eml2pdf input/ output/ --unsafe
```

## Technical Details

### Sanitization Process

1. HTML content is parsed using BeautifulSoup.
2. Risky tags are found and completely removed with `.decompose()`.
3. Attributes are selectively filtered or modified.
4. The sanitized HTML is converted back to a string.

### Integration with PDF Generation

The sanitization occurs in the `generate_pdf()` function in eml2pdf/libeml2pdf.py:

```python
def generate_pdf(html_content: str, outfile_path: Path, infile: Path,
                 debug_html: bool = False, page: str = 'a4',
                 unsafe: bool = False):
    """Convert HTML to PDF."""
    if not unsafe:
        html_content = security.sanitize_html(html_content)
    # ... PDF generation continues ...
```

This ensures that all HTML content is sanitized immediately before PDF
rendering, regardless of the source.

## Limitations

Above is a listing of what we do and you have access to the code. Judge for
yourself and use on your discretion. Suggestions are more than welcome!

## Recommendations

1. **Keep Default Security**: Always use the default secure mode unless you
   have a specific, trusted use case
2. **Verify Sources**: Only process EML files from trusted sources
3. **Sandbox Processing**: Consider running eml2pdf in a sandboxed environment
   when processing untrusted emails. With no Internet access.
4. **Update Dependencies**: Keep BeautifulSoup, WeasyPrint, and other
   dependencies up to date

## Related Files

- Security implementation: `eml2pdf/security.py`
- Security integration: `eml2pdf/libeml2pdf.py`
- CLI unsafe flag: `eml2pdf/eml2pdf.py`
