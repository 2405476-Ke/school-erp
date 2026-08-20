import re

file_path = "src/app/App.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '// import { apiGet, apiPost } from "@/services/api"; // Uncomment when backend is ready',
    'import { apiGet, apiPost } from "../services/api";'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed imports")
