@echo off
setlocal enabledelayedexpansion
cd /d C:\Users\Clone\Desktop\Zawadi\work

echo Initializing git repository...
"C:\Program Files\Git\bin\git.exe" init

echo Configuring user name...
"C:\Program Files\Git\bin\git.exe" config user.name "Your Name"

echo Configuring user email...
"C:\Program Files\Git\bin\git.exe" config user.email "your.email@gmail.com"

echo Adding all files...
"C:\Program Files\Git\bin\git.exe" add .

echo Creating initial commit...
"C:\Program Files\Git\bin\git.exe" commit -m "Initial commit: Nambale ERP frontend and backend integration with 6 gap components"

echo Adding remote origin...
"C:\Program Files\Git\bin\git.exe" remote add origin https://github.com/2405476-Ke/school-erp.git

echo Setting main branch...
"C:\Program Files\Git\bin\git.exe" branch -M main

echo Pushing to GitHub (you will be prompted to authenticate)...
"C:\Program Files\Git\bin\git.exe" push -u origin main

pause
