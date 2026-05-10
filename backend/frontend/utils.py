import re
import shutil
from pathlib import Path


def update_base_href(index_html_path: str | Path, base_href: str) -> None:
    """Update the <base href="..."> tag in an index.html file."""
    path = Path(index_html_path)
    if not path.exists():
        return

    clean_href = base_href.strip()
    if not clean_href.startswith("/"):
        clean_href = "/" + clean_href
    if not clean_href.endswith("/"):
        clean_href = clean_href + "/"

    content = path.read_text(encoding="utf-8")
    pattern = r'(<base\s+[^>]*href=["\'])([^"\']*)(["\'][^>]*>)'
    new_content = re.sub(pattern, r"\1" + clean_href + r"\3", content)
    if content != new_content:
        path.write_text(new_content, encoding="utf-8")


def setup_url_base_folder(frontend_dir: Path, url_base: str) -> Path:
    """
    Create a subfolder named after url_base inside frontend_dir containing a
    patched index.html with <base href="/{url_base}/">.

    Only index.html is written here. All other static assets are served
    directly from frontend_dir by the catch-all route, so no copying is needed.

    Returns the path to the created subfolder.
    """
    url_base_name = url_base.strip("/")
    subfolder = frontend_dir / url_base_name
    subfolder.mkdir(exist_ok=True)

    root_index = frontend_dir / "index.html"
    sub_index = subfolder / "index.html"
    if root_index.exists():
        shutil.copy2(root_index, sub_index)
        update_base_href(sub_index, url_base)

    return subfolder
