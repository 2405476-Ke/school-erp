@echo off
cd /d C:\Users\Clone\Desktop\Zawadi\work
echo Resolving merge conflicts...
"C:\Program Files\Git\bin\git.exe" checkout --ours .gitignore README.md
"C:\Program Files\Git\bin\git.exe" add .gitignore README.md
echo Committing merge...
"C:\Program Files\Git\bin\git.exe" commit -m "Merge remote changes and resolve conflicts"
echo Pushing to GitHub...
"C:\Program Files\Git\bin\git.exe" push -u origin main
echo Push complete!
pause
