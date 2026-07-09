import os
import sys
import re
import mimetypes
import urllib.parse
import posixpath
from http.server import HTTPServer, BaseHTTPRequestHandler
import markdown

# Configurable paths
DOCS_ROOT = os.path.realpath(os.environ.get("DOCS_ROOT", "/docs"))
PORT = int(os.environ.get("PORT", "8000"))

# Read layout template
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'layout.html')
try:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        TEMPLATE = f.read()
except OSError:
    print(f"Error: Could not read template from {TEMPLATE_PATH}", file=sys.stderr)
    TEMPLATE = "<html><body>{{ content }}</body></html>"


def is_safe_path(path):
    """Ensure the path is within the DOCS_ROOT directory to prevent traversal."""
    real_path = os.path.realpath(path)
    return real_path == DOCS_ROOT or real_path.startswith(DOCS_ROOT + os.sep)


def get_breadcrumbs(url_path):
    """Generate beautiful navigation breadcrumbs."""
    parts = [p for p in url_path.split('/') if p]
    breadcrumbs_html = '<a href="/">Home</a>'
    
    current_acc = ""
    for i, part in enumerate(parts):
        current_acc += f"/{part}"
        breadcrumbs_html += ' <span class="separator">/</span> '
        if i == len(parts) - 1:
            breadcrumbs_html += f'<span class="current">{part}</span>'
        else:
            breadcrumbs_html += f'<a href="{current_acc}">{part}</a>'
            
    return breadcrumbs_html


def build_tree(path):
    """Recursively build a tree of folders and markdown files."""
    items = []
    try:
        names = os.listdir(path)
    except OSError:
        return []
        
    for name in names:
        if name.startswith('.'):
            continue
        if name in ('node_modules', 'venv', '.git', '__pycache__', 'data'):
            continue
            
        full_path = os.path.join(path, name)
        rel_path = os.path.relpath(full_path, DOCS_ROOT)
        
        if os.path.isdir(full_path):
            children = build_tree(full_path)
            # Only list directory if it contains markdown files or subdirs with markdown files
            if children:
                items.append({
                    'name': name,
                    'type': 'dir',
                    'rel_path': rel_path.replace(os.sep, '/'),
                    'children': children
                })
        elif name.endswith('.md'):
            url_name = name[:-3]
            # Handle root readme differently or filter it
            if url_name.lower() in ('readme', 'index') and rel_path == name:
                # We skip showing root readme directly in sidebar tree to prevent clutter,
                # as it is already mapped to the Home button.
                continue
                
            # Form clean url
            url_path = os.path.splitext(rel_path)[0]
            url = '/' + url_path.replace(os.sep, '/')
            
            # If it's a subdirectory README, we want to link it to the folder URL
            if url_name.lower() in ('readme', 'index'):
                parent_dir = os.path.dirname(rel_path)
                url = '/' + parent_dir.replace(os.sep, '/') if parent_dir else '/'
                display_name = os.path.basename(parent_dir) if parent_dir else 'Home'
            else:
                display_name = url_name
                
            items.append({
                'name': display_name,
                'type': 'file',
                'url': url,
                'rel_path': rel_path.replace(os.sep, '/')
            })
            
    # Sort folders first, then files
    items.sort(key=lambda x: (0 if x['type'] == 'dir' else 1, x['name'].lower()))
    return items


def render_tree(tree, active_url):
    """Render the built tree into HTML nested ul/details list."""
    if not tree:
        return ""
        
    html = '<ul class="nav-list">'
    for item in tree:
        if item['type'] == 'dir':
            # Check if active URL is nested inside this directory
            active_clean = active_url.lstrip('/')
            is_open = active_clean.startswith(item['rel_path'] + '/') or active_clean == item['rel_path']
            open_attr = ' open' if is_open else ''
            
            html += f'<li class="nav-dir"><details{open_attr}><summary><span class="icon">📁</span> {item["name"]}</summary>'
            html += render_tree(item['children'], active_url)
            html += '</details></li>'
        else:
            is_active = ' active' if active_url == item['url'] else ''
            html += f'<li class="nav-file{is_active}"><a href="{item["url"]}"><span class="icon">📄</span> {item["name"]}</a></li>'
    html += '</ul>'
    return html


def process_alerts(html):
    """Convert GitHub-style alerts > [!NOTE] into beautiful callouts."""
    pattern = re.compile(
        r'<blockquote>\s*<p>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](.*?)</p>(.*?)</blockquote>',
        re.DOTALL | re.IGNORECASE
    )
    
    def replace_alert(match):
        alert_type = match.group(1).upper()
        content = match.group(2).strip()
        rest = match.group(3).strip()
        
        # Colors, icons and styling
        alerts = {
            'NOTE': ('#3b82f6', 'ℹ️', 'Note', 'rgba(59, 130, 246, 0.08)'),
            'TIP': ('#10b981', '💡', 'Tip', 'rgba(16, 185, 129, 0.08)'),
            'IMPORTANT': ('#8b5cf6', '📢', 'Important', 'rgba(139, 92, 246, 0.08)'),
            'WARNING': ('#f59e0b', '⚠️', 'Warning', 'rgba(245, 158, 11, 0.08)'),
            'CAUTION': ('#ef4444', '🚨', 'Caution', 'rgba(239, 68, 68, 0.08)')
        }
        
        color, icon, title, bg = alerts.get(alert_type, ('#64748b', 'ℹ️', 'Note', 'rgba(100, 116, 139, 0.08)'))
        
        full_content = content
        if rest:
            full_content += f"<p>{rest}</p>"
            
        return f'''<div class="alert-box alert-{alert_type.lower()}" style="border-left: 4px solid {color}; background-color: {bg}; margin: 1.5rem 0; padding: 1rem 1.25rem; border-radius: 6px;">
            <div class="alert-header" style="display: flex; align-items: center; gap: 0.5rem; font-weight: 600; color: {color}; margin-bottom: 0.5rem; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.05em;">
                <span>{icon}</span>
                <span>{title}</span>
            </div>
            <div class="alert-body" style="font-size: 0.975rem; line-height: 1.6; color: var(--text-main); opacity: 0.9;">{full_content}</div>
        </div>'''
        
    return pattern.sub(replace_alert, html)


def generate_folder_index(folder_path, rel_url_path):
    """Renders a directory list when no index README is present."""
    try:
        names = os.listdir(folder_path)
    except OSError:
        return "<h1>Error loading directory</h1>"
        
    names.sort()
    
    html = f"<h1>Index of {rel_url_path}</h1>"
    html += "<ul class='folder-index-list'>"
    
    if rel_url_path != '/':
        parent = posixpath.dirname(rel_url_path)
        html += f"<li><span class='icon'>📁</span> <a href='{parent}'>.. (Parent Directory)</a></li>"
        
    for name in names:
        if name.startswith('.') or name in ('node_modules', 'venv', '.git', '__pycache__', 'data'):
            continue
            
        full_p = os.path.join(folder_path, name)
        is_dir = os.path.isdir(full_p)
        
        if is_dir:
            url = posixpath.join(rel_url_path, name)
            html += f"<li><span class='icon'>📁</span> <a href='{url}'>{name}/</a></li>"
        elif name.endswith('.md'):
            url_name = name[:-3]
            url = posixpath.join(rel_url_path, url_name)
            html += f"<li><span class='icon'>📄</span> <a href='{url}'>{url_name}</a></li>"
        else:
            url = posixpath.join(rel_url_path, name)
            html += f"<li><span class='icon'>📎</span> <a href='{url}'>{name}</a></li>"
            
    html += "</ul>"
    return html


class DocsHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to log cleanly to stdout/stderr
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))

    def resolve_url_to_file(self, path_str):
        """Maps HTTP path to filesystem path inside DOCS_ROOT."""
        path_str = urllib.parse.unquote(path_str)
        parsed = urllib.parse.urlparse(path_str)
        clean_path = posixpath.normpath(parsed.path)
        
        if clean_path.startswith('../') or '/../' in clean_path:
            return None, None, False
            
        rel_path = clean_path.lstrip('/')
        
        # If accessing root directory
        if not rel_path:
            for name in ('README.md', 'index.md', 'readme.md', 'README.markdown', 'readme.markdown'):
                full_p = os.path.join(DOCS_ROOT, name)
                if os.path.isfile(full_p):
                    return full_p, '/', True
            # No root readme, return DOCS_ROOT directory for auto-index
            return DOCS_ROOT, '/', False

        full_p = os.path.join(DOCS_ROOT, rel_path)
        
        # 1. Direct file check
        if os.path.isfile(full_p):
            is_md = full_p.endswith('.md') or full_p.endswith('.markdown')
            return full_p, '/' + rel_path, is_md
            
        # 2. Check path + .md
        if not rel_path.endswith('.md'):
            md_path = full_p + '.md'
            if os.path.isfile(md_path):
                return md_path, '/' + rel_path, True
                
        # 3. Check directory
        if os.path.isdir(full_p):
            for name in ('README.md', 'index.md', 'readme.md'):
                sub_p = os.path.join(full_p, name)
                if os.path.isfile(sub_p):
                    return sub_p, '/' + rel_path, True
            # Folder without index README, serve directory index page
            return full_p, '/' + rel_path, False

        return None, '/' + rel_path, False

    def do_GET(self):
        filepath, active_url, is_md = self.resolve_url_to_file(self.path)
        
        if not filepath or not is_safe_path(filepath):
            self.render_error(404, "Page Not Found", active_url)
            return

        # Serve static asset
        if not is_md and os.path.isfile(filepath):
            self.serve_static_file(filepath)
            return

        # Serve Markdown or Directory Index
        if is_md:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    md_content = f.read()
            except OSError:
                self.render_error(500, "Internal Server Error - Could not read file", active_url)
                return
                
            # Render Markdown
            md = markdown.Markdown(extensions=['extra', 'toc', 'nl2br'])
            html_content = md.convert(md_content)
            html_content = process_alerts(html_content)
            
            toc_html = md.toc
            has_toc = 'href=' in toc_html
            
            title = os.path.basename(filepath)
            if title.endswith('.md'):
                title = title[:-3]
            if title.lower() in ('readme', 'index'):
                parent_dir = os.path.basename(os.path.dirname(filepath))
                title = parent_dir if parent_dir else "Home"
        else:
            # Renders folder directory index
            html_content = generate_folder_index(filepath, active_url)
            toc_html = ""
            has_toc = False
            title = os.path.basename(filepath) or "Index"

        # Generate Sidebar tree
        sidebar_tree_data = build_tree(DOCS_ROOT)
        sidebar_html = render_tree(sidebar_tree_data, active_url)
        
        # Build breadcrumbs
        breadcrumbs = get_breadcrumbs(active_url)
        
        # Render page using layout
        page_html = TEMPLATE
        page_html = page_html.replace('{{ title }}', title)
        page_html = page_html.replace('{{ home_active }}', ' active' if active_url == '/' else '')
        page_html = page_html.replace('{{ sidebar_tree }}', sidebar_html)
        page_html = page_html.replace('{{ breadcrumbs }}', breadcrumbs)
        page_html = page_html.replace('{{ content }}', html_content)
        page_html = page_html.replace('{{ toc }}', toc_html)
        page_html = page_html.replace('{{ grid_class }}', ' has-toc' if has_toc else '')
        
        # Conditional template logic for TOC
        if has_toc:
            page_html = page_html.replace('{% if has_toc %}', '').replace('{% endif %}', '')
        else:
            page_html = re.sub(r'{% if has_toc %}.*?{% endif %}', '', page_html, flags=re.DOTALL)
            
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()
        self.wfile.write(page_html.encode('utf-8'))

    def serve_static_file(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
        except OSError:
            self.send_error(404, "File not found")
            return
            
        self.send_response(200)
        ctype, _ = mimetypes.guess_type(filepath)
        if not ctype:
            ctype = 'application/octet-stream'
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'public, max-age=600')
        self.end_headers()
        self.wfile.write(content)

    def render_error(self, code, message, active_url):
        # Render a nice formatted error inside the layout
        error_html = f'''
        <div style="text-align: center; padding: 4rem 2rem;">
            <h1 style="font-size: 5rem; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;">{code}</h1>
            <p style="font-size: 1.25rem; color: var(--text-muted); margin-bottom: 2rem;">{message}</p>
            <a href="/" style="display: inline-block; background: var(--accent-gradient); color: white; padding: 0.75rem 1.5rem; border-radius: 6px; font-weight: 600; text-decoration: none;">Go Home</a>
        </div>
        '''
        sidebar_tree_data = build_tree(DOCS_ROOT)
        sidebar_html = render_tree(sidebar_tree_data, active_url)
        breadcrumbs = get_breadcrumbs(active_url)
        
        page_html = TEMPLATE
        page_html = page_html.replace('{{ title }}', f"Error {code}")
        page_html = page_html.replace('{{ home_active }}', '')
        page_html = page_html.replace('{{ sidebar_tree }}', sidebar_html)
        page_html = page_html.replace('{{ breadcrumbs }}', breadcrumbs)
        page_html = page_html.replace('{{ content }}', error_html)
        page_html = page_html.replace('{{ toc }}', '')
        page_html = page_html.replace('{{ grid_class }}', '')
        page_html = re.sub(r'{% if has_toc %}.*?{% endif %}', '', page_html, flags=re.DOTALL)
        
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page_html.encode('utf-8'))


def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, DocsHTTPHandler)
    print(f"Starting markdown docs server on port {PORT}...")
    print(f"Serving files from {DOCS_ROOT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print("\nStopping server.")

if __name__ == '__main__':
    run_server()
