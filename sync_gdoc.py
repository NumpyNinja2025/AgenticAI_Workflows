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

# --- FINAL, ROBUST Conversion Logic ---
def parse_doc_to_md(content):
    """
    Parses Google Doc content to structurally correct Markdown,
    handling headings, lists, links, and styling.
    """
    markdown_lines = []
    list_counters = {}

    for element in content:
        if 'paragraph' in element:
            paragraph = element.get('paragraph')
            elements = paragraph.get('elements', [])

            # Handle Horizontal Rules, which are a type of paragraph element
            if elements and 'horizontalRule' in elements[0]:
                markdown_lines.append('---')
                continue

            # Handle empty paragraphs (used for spacing)
            if len(elements) == 1 and elements[0].get('textRun', {}).get('content') == '\n':
                markdown_lines.append('')
                continue

            # Build the Markdown for this single paragraph
            current_line_parts = []
            
            # Process all text runs in this paragraph
            for el in elements:
                if 'textRun' in el:
                    text_run = el.get('textRun')
                    text_content = text_run.get('content', '')
                    
                    # Skip the automatic newline character that ends a paragraph
                    if text_content == '\n':
                        continue
                    
                    # Handle soft line breaks (Shift+Enter) if they exist
                    text_content = text_content.replace('\v', '  \n')

                    text_style = text_run.get('textStyle', {})
                    
                    # Apply styles from the inside out
                    processed_content = text_content
                    if text_style.get('bold'):
                        processed_content = f"**{processed_content}**"
                    
                    if text_style.get('link'):
                        processed_content = f"[{processed_content}]({text_style['link']['url']})"

                    current_line_parts.append(processed_content)
            
            current_line = "".join(current_line_parts)

            # Handle Numbered Lists
            if 'bullet' in paragraph:
                list_id = paragraph['bullet']['listId']
                nesting_level = paragraph['bullet'].get('nestingLevel', 0)
                indent = "  " * nesting_level
                
                # A simple way to manage list counters
                if list_id not in list_counters:
                    list_counters[list_id] = 0
                list_counters[list_id] += 1
                
                current_line = f"{indent}{list_counters[list_id]}. {current_line}"
            else:
                # Reset counters when we exit a list
                list_counters = {}

            # Handle Paragraph Styles (Headings)
            p_style = paragraph.get('paragraphStyle', {})
            if 'namedStyleType' in p_style:
                style = p_style['namedStyleType']
                if style == 'HEADING_1':
                    current_line = f"# {current_line}"
                elif style == 'HEADING_2':
                    current_line = f"## {current_line}"
                elif style == 'HEADING_3':
                    current_line = f"### {current_line}"
                elif style == 'HEADING_4':
                    current_line = f"#### {current_line}"

            markdown_lines.append(current_line)

    return "\n".join(markdown_lines)

# --- Main Execution ---
markdown_content = parse_doc_to_md(content)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)

print("Successfully synced Google Doc to README.md")
