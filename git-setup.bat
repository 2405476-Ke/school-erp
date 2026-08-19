@echo off
cd /d C:\Users\Clone\Desktop\Zawadi\work
"C:\Program Files\Git\bin\git.exe" init
"C:\Program Files\Git\bin\git.exe" config user.name "Developer"
"C:\Program Files\Git\bin\git.exe" config user.email "dev@zawadi.com"
"C:\Program Files\Git\bin\git.exe" add .
"C:\Program Files\Git\bin\git.exe" commit -m "Initial commit: Nambale ERP frontend and backend integration with all 6 gap components"
pause
