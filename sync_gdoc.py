import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Configuration ---
DOC_ID = os.getenv("DOC_ID")
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# --- Authentication ---
try:
    creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build('docs', 'v1', credentials=creds)
except (json.JSONDecodeError, TypeError) as e:
    print(f"Error loading Google credentials: {e}")
    exit(1)

# --- Fetch Document Content ---
try:
    doc = service.documents().get(documentId=DOC_ID).execute()
    content = doc.get('body').get('content')
except Exception as e:
    print(f"Error fetching Google Doc: {e}")
    exit(1)

# --- NEW Conversion Logic ---
def parse_doc_to_md(content):
    """
    Parses Google Doc content and converts it to structurally correct Markdown.
    """
    markdown_lines = []
    list_counters = {}  # To keep track of numbering for different lists

    for element in content:
        # --- Handle Horizontal Rules ---
        if 'horizontalRule' in element:
            markdown_lines.append('---')
            continue

        # --- Handle Paragraphs (includes text, lists, and empty lines) ---
        if 'paragraph' in element:
            paragraph = element.get('paragraph')
            elements = paragraph.get('elements', [])
            
            # Check for empty paragraphs which are used for spacing
            # An empty paragraph has one element with only a newline character
            if len(elements) == 1 and elements[0].get('textRun', {}).get('content') == '\n':
                markdown_lines.append('')
                continue
            
            line_parts = []
            
            # Handle list items (numbered lists)
            bullet = paragraph.get('bullet')
            if bullet and bullet.get('listId'):
                list_id = bullet.get('listId')
                # Increment the counter for this specific list
                list_counters[list_id] = list_counters.get(list_id, 0) + 1
                # Add the list marker to the beginning of the line
                line_parts.append(f"{list_counters[list_id]}. ")
            
            # Process each text run within the paragraph
            for el in elements:
                if 'textRun' in el:
                    text_run = el.get('textRun')
                    text_content = text_run.get('content', '')
                    text_style = text_run.get('textStyle', {})
                    
                    # Ignore pure newline characters within a paragraph
                    if text_content == '\n':
                        continue

                    # Apply formatting styles only to this specific text run
                    if text_style.get('bold'):
                        text_content = f"**{text_content}**"
                    
                    if text_style.get('link'):
                        url = text_style['link']['url']
                        # Clean the text content to prevent broken Markdown links
                        clean_text_content = text_content.replace('\n', ' ').strip()
                        # Re-apply bolding if it was there
                        if text_style.get('bold'):
                           clean_text_content = f"**{clean_text_content}**"
                        text_content = f"[{clean_text_content}]({url})"

                    line_parts.append(text_content)
            
            # Join all parts of the line and add to our output
            if line_parts:
                markdown_lines.append("".join(line_parts))

    return "\n".join(markdown_lines)


# --- Main Execution ---
markdown_content = parse_doc_to_md(content)

# Write to README.md
with open("README.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)

print("Successfully synced Google Doc to README.md")
