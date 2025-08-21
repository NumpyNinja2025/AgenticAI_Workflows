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

# --- Conversion Logic ---
def parse_doc_to_md(content):
    """
    Parses Google Doc content and converts it to Markdown.
    """
    markdown_output = []
    list_counters = {}  # To keep track of numbering for different lists

    for element in content:
        if 'paragraph' in element:
            paragraph = element.get('paragraph')
            line_text = ""

            # Handle list items (numbered lists)
            bullet = paragraph.get('bullet')
            if bullet and bullet.get('listId'):
                list_id = bullet.get('listId')
                # Increment the counter for this specific list
                list_counters[list_id] = list_counters.get(list_id, 0) + 1
                # The glyph for a numbered list is usually '%1'. We format it.
                # Assuming simple numbered lists for now.
                line_text += f"{list_counters[list_id]}. "
            
            # Process text runs within the paragraph
            elements = paragraph.get('elements', [])
            for el in elements:
                if 'textRun' in el:
                    text_run = el.get('textRun')
                    text_content = text_run.get('content', '')
                    text_style = text_run.get('textStyle', {})

                    # Strip out vertical tabs which can appear
                    text_content = text_content.replace('\v', '')

                    # Apply formatting
                    if text_style.get('bold'):
                        text_content = f"**{text_content}**"
                    
                    if text_style.get('link'):
                        url = text_style['link']['url']
                        # Remove newline characters from the link text to prevent broken links
                        clean_text_content = text_content.replace('\n', ' ').strip()
                        text_content = f"[{clean_text_content}]({url})"

                    line_text += text_content

            # Add the processed line to our output list
            # We strip trailing whitespace and handle newlines
            # Empty paragraphs in GDoc will result in empty lines for spacing
            markdown_output.append(line_text.rstrip())

    return "\n".join(markdown_output)


# --- Main Execution ---
markdown_content = parse_doc_to_md(content)

# Write to README.md
with open("README.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)

print("Successfully synced Google Doc to README.md")
