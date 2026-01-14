import re
from pathlib import Path


def update_base_href(index_html_path: str | Path, base_href: str):
    """
    Updates the <base href="..."> tag in index.html to a specific absolute path.
    Handles replacing './', '/', or any existing value.
    """
    path = Path(index_html_path)

    if not path.exists():
        return

    # 1. Normalize the base_href (e.g., "trailarr" -> "/trailarr/")
    clean_href = base_href.strip()
    if not clean_href.startswith("/"):
        clean_href = "/" + clean_href
    if not clean_href.endswith("/"):
        clean_href = clean_href + "/"

    # 2. Read the file
    content = path.read_text(encoding="utf-8")

    # 3. Improved Regex:
    # Finds <base ... href="./" ...> or <base ... href="/" ...>
    # It targets the value inside the quotes for the 'href' attribute specifically within a <base> tag.
    pattern = r'(<base\s+[^>]*href=["\'])([^"\']*)(["\'][^>]*>)'

    # We keep group 1 (tag start + href=") and group 3 (closing quote + tag end)
    # and swap group 2 with our clean_href.
    new_content = re.sub(pattern, r"\1" + clean_href + r"\3", content)

    # 4. Save if changed
    if content != new_content:
        path.write_text(new_content, encoding="utf-8")
        print(f"Baking Base HREF: Swapped existing value for '{clean_href}'")
