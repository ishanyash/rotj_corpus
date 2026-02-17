"""Google Doc read/write/clear operations."""

import datetime


def _log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {timestamp} - {message}")


def clear_document(docs_service, doc_id):
    """Delete all content from the Google Doc before inserting a new edition."""
    _log("Clearing existing document content")
    doc = docs_service.documents().get(documentId=doc_id).execute()
    body = doc.get('body', {})
    content = body.get('content', [])

    if len(content) <= 1:
        _log("Document is already empty")
        return

    # Find the end index of the document body
    end_index = content[-1].get('endIndex', 1)

    if end_index > 2:
        requests = [{
            'deleteContentRange': {
                'range': {
                    'startIndex': 1,
                    'endIndex': end_index - 1,  # Preserve the final newline
                }
            }
        }]
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests},
        ).execute()
        _log("Document cleared successfully")


def write_to_doc(docs_service, doc_id, api_requests):
    """Execute a list of Google Docs API requests (insert + formatting)."""
    if not api_requests:
        _log("No requests to execute", "WARNING")
        return False

    _log(f"Writing to Google Doc ({len(api_requests)} API requests)")
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': api_requests},
    ).execute()
    _log("Google Doc updated successfully")
    return True
