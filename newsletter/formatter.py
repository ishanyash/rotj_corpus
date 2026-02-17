"""Google Docs API rich formatting — builds structured API requests for headings, bold, links, etc."""


class DocFormatter:
    """Builds a list of Google Docs API requests for rich document formatting.

    Works in two passes:
    1. Accumulates plain text (no markdown symbols).
    2. Tracks formatting operations (headings, bold, links, dividers) with exact character ranges.

    After all content is added, call build_requests() to get the complete list
    of API requests: one insertText followed by all formatting operations.
    """

    def __init__(self):
        self._text_parts = []
        self._format_ops = []
        self._cursor = 1  # Google Docs body starts at index 1

    def _advance(self, text):
        """Record text and advance the cursor."""
        self._text_parts.append(text)
        length = len(text)
        start = self._cursor
        self._cursor += length
        return start, self._cursor

    def add_heading(self, text, level=1):
        """Add a heading (H1, H2, or H3)."""
        start, end = self._advance(text + '\n')
        heading_map = {1: 'HEADING_1', 2: 'HEADING_2', 3: 'HEADING_3'}
        self._format_ops.append({
            'updateParagraphStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'paragraphStyle': {'namedStyleType': heading_map.get(level, 'HEADING_1')},
                'fields': 'namedStyleType',
            }
        })

    def add_text(self, text):
        """Add plain text."""
        self._advance(text)

    def add_newline(self):
        """Add a newline character."""
        self._advance('\n')

    def add_bold_text(self, text):
        """Add bold text (no trailing newline)."""
        start, end = self._advance(text)
        self._format_ops.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': {'bold': True},
                'fields': 'bold',
            }
        })

    def add_italic_text(self, text):
        """Add italic text."""
        start, end = self._advance(text)
        self._format_ops.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': {'italic': True},
                'fields': 'italic',
            }
        })

    def add_link(self, display_text, url):
        """Add a clickable hyperlink."""
        start, end = self._advance(display_text)
        self._format_ops.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': {
                    'link': {'url': url},
                    'foregroundColor': {
                        'color': {'rgbColor': {'red': 0.06, 'green': 0.45, 'blue': 0.85}}
                    },
                },
                'fields': 'link,foregroundColor',
            }
        })

    def add_bold_link(self, display_text, url):
        """Add a bold clickable hyperlink."""
        start, end = self._advance(display_text)
        self._format_ops.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': {
                    'bold': True,
                    'link': {'url': url},
                    'foregroundColor': {
                        'color': {'rgbColor': {'red': 0.06, 'green': 0.45, 'blue': 0.85}}
                    },
                },
                'fields': 'bold,link,foregroundColor',
            }
        })

    def add_horizontal_rule(self):
        """Add a visual divider using a bottom-bordered empty paragraph."""
        start, end = self._advance('\n')
        self._format_ops.append({
            'updateParagraphStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'paragraphStyle': {
                    'borderBottom': {
                        'color': {'color': {'rgbColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}},
                        'width': {'magnitude': 1, 'unit': 'PT'},
                        'padding': {'magnitude': 6, 'unit': 'PT'},
                        'dashStyle': 'SOLID',
                    }
                },
                'fields': 'borderBottom',
            }
        })

    def add_colored_text(self, text, red=0.0, green=0.0, blue=0.0):
        """Add text with a custom color."""
        start, end = self._advance(text)
        self._format_ops.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': {
                    'foregroundColor': {
                        'color': {'rgbColor': {'red': red, 'green': green, 'blue': blue}}
                    }
                },
                'fields': 'foregroundColor',
            }
        })

    def add_bullet_item(self, text):
        """Add a line of text. Bullet formatting is applied separately via add_bullets_to_range."""
        self._advance(text + '\n')

    def add_bullets_to_range(self, start_index, end_index):
        """Apply bullet list formatting to a range of paragraphs."""
        self._format_ops.append({
            'createParagraphBullets': {
                'range': {'startIndex': start_index, 'endIndex': end_index},
                'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE',
            }
        })

    def build_requests(self):
        """Return the complete list of API requests: insert text, then apply formatting."""
        full_text = ''.join(self._text_parts)
        if not full_text:
            return []

        insert_request = {
            'insertText': {
                'location': {'index': 1},
                'text': full_text,
            }
        }
        return [insert_request] + self._format_ops
