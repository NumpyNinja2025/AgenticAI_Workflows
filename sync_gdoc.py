import os
import requests
import pypandoc

DOC_ID = os.getenv("GOOGLE_DOC_ID")
OUTPUT_FILE = "README.md"

# Export Google Doc as HTML
url = f"https://docs.google.com/document/d/{DOC_ID}/export?format=html"
response = requests.get(url)
response.raise_for_status()

html_content = response.text

# Convert HTML → Markdown
markdown_content = pypandoc.convert_text(html_content, "md", format="html")

# Save to README.md
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(markdown_content)

print("README.md updated successfully!")
