@echo off
setlocal enabledelayedexpansion

echo 💾 Starting ARTHA database backup...

REM Create backup directory if it doesn't exist
if not exist backups mkdir backups

REM Generate backup filename with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
set "BACKUP_FILE=backups\artha_backup_%TIMESTAMP%.gz"

echo Creating backup: %BACKUP_FILE%

REM Create database backup
docker exec artha-mongo-prod mongodump --authenticationDatabase=admin --db=artha_prod --gzip --archive=/tmp/backup.gz

REM Copy backup from container to host
docker cp artha-mongo-prod:/tmp/backup.gz %BACKUP_FILE%

REM Clean up temporary file in container
docker exec artha-mongo-prod rm /tmp/backup.gz

echo ✅ Backup completed successfully!
echo Backup file: %BACKUP_FILE%

REM Keep only last 7 backups
echo Cleaning up old backups...
for /f "skip=7 delims=" %%i in ('dir /b /o-d backups\artha_backup_*.gz 2^>nul') do del "backups\%%i"

echo Backup process completed