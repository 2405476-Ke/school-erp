@echo off
cd /d C:\Users\Clone\Desktop\Zawadi\work

echo Adding backend to git...
"C:\Program Files\Git\bin\git.exe" add backend/

echo Committing backend...
"C:\Program Files\Git\bin\git.exe" commit -m "Add FastAPI backend with all 6 gap components (LeavePassApproval, ExeatQueue, DormAllocation, GateAuditLog, StockIssuance, BatchReport) to monorepo"

echo Pushing to GitHub...
"C:\Program Files\Git\bin\git.exe" push -u origin main

echo Complete!
pause
