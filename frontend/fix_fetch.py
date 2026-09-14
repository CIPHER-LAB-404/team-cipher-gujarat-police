import re

filepath = 'e:/GOG_Hackathon/frontend/app.js'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace fetch('/api/...) or fetch(`/api/...) with window.Auth.apiFetch(...)
content = re.sub(r"fetch\((['\"`])/api/", r"window.Auth.apiFetch(\1/api/", content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('app.js fetch calls updated')
