from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
import markdown
import os


class MarkdownWebViewer(QDialog):
    """
    Displays a Markdown file rendered as HTML using QWebEngineView,
    with custom CSS support and full Obsidian-style markdown.
    """
    def __init__(self, md_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Manual")
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        self.load_markdown(md_path)

    def load_markdown(self, md_path: str):
        if not os.path.exists(md_path):
            html = f"<h1>File not found</h1><p>{md_path}</p>"
            self.web_view.setHtml(html)
            return

        with open(md_path, 'r', encoding='utf-8') as f:
            md_text = f.read()

        # Convert markdown to HTML
        html_body = markdown.markdown(
            md_text,
            extensions=['fenced_code', 'tables', 'toc', 'attr_list', 'admonition']
        )

        # Load a custom CSS if available
        css_path = os.path.join(os.path.dirname(__file__), "manual.css")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                css = f.read()
        else:
            css = "body { font-family: sans-serif; padding: 2em; } table { border-collapse: collapse; } th, td { border: 1px solid #ccc; padding: 0.5em; }"

        html = f"""
        <html>
        <head>
        <meta charset="utf-8">
        <style>{css}</style>
        </head>
        <body>{html_body}</body>
        </html>
        """
        self.web_view.setHtml(html, QUrl("file://" + os.path.abspath(md_path)))
