import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

DOC_ID = os.getenv("DOC_ID")
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
service = build('docs', 'v1', credentials=creds)

doc = service.documents().get(documentId=DOC_ID).execute()
content = doc.get('body').get('content')

text_output = []
for element in content:
    if 'paragraph' in element:
        for el in element['paragraph']['elements']:
            if 'textRun' in el:
                text_output.append(el['textRun']['content'])

with open("README.md", "w", encoding="utf-8") as f:
    f.write("".join(text_output))
