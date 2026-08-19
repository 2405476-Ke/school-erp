@echo off
cd /d C:\Users\Clone\Desktop\Zawadi\work
echo Pulling remote changes...
"C:\Program Files\Git\bin\git.exe" pull origin main --allow-unrelated-histories
echo Pushing to GitHub...
"C:\Program Files\Git\bin\git.exe" push -u origin main
echo Done!
pause
