import re

file_path = "src/app/App.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace literal \n that was accidentally injected
content = content.replace('\\n', '\n')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed literal newlines")
