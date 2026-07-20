# PowerShell script to upload files to 0x0.st

$modelFile = "led_model_quantized.pkl.gz"
$tokenizerFile = "tokenizer.pkl.gz"

Write-Host "Uploading files to 0x0.st..." -ForegroundColor Cyan
Write-Host ""

# Upload model file
if (Test-Path $modelFile) {
    Write-Host "Uploading $modelFile [202.35 MB]..." -ForegroundColor Yellow
    try {
        $boundary = [System.Guid]::NewGuid().ToString()
        $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $modelFile))
        $bodyLines = @(
            "--$boundary",
            "Content-Disposition: form-data; name=`"file`"; filename=`"$modelFile`"",
            "Content-Type: application/octet-stream",
            "",
            [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes),
            "--$boundary--"
        )
        $body = $bodyLines -join "`r`n"
        $modelResponse = Invoke-WebRequest -Uri "https://0x0.st" -Method Post -Body $body -ContentType "multipart/form-data; boundary=$boundary" -ErrorAction Stop
        $modelUrl = $modelResponse.Content.Trim()
        Write-Host "✓ Model file uploaded successfully!" -ForegroundColor Green
        Write-Host "URL: $modelUrl" -ForegroundColor Cyan
        Write-Host ""
        
        # Save URL to file
        $modelUrl | Out-File -FilePath "model_url.txt" -Encoding utf8
    } catch {
        Write-Host "✗ Failed to upload model file: $_" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Model file not found: $modelFile" -ForegroundColor Red
}

# Upload tokenizer file
if (Test-Path $tokenizerFile) {
    Write-Host "Uploading $tokenizerFile [0.53 MB]..." -ForegroundColor Yellow
    try {
        $boundary = [System.Guid]::NewGuid().ToString()
        $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $tokenizerFile))
        $bodyLines = @(
            "--$boundary",
            "Content-Disposition: form-data; name=`"file`"; filename=`"$tokenizerFile`"",
            "Content-Type: application/octet-stream",
            "",
            [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes),
            "--$boundary--"
        )
        $body = $bodyLines -join "`r`n"
        $tokenizerResponse = Invoke-WebRequest -Uri "https://0x0.st" -Method Post -Body $body -ContentType "multipart/form-data; boundary=$boundary" -ErrorAction Stop
        $tokenizerUrl = $tokenizerResponse.Content.Trim()
        Write-Host "✓ Tokenizer file uploaded successfully!" -ForegroundColor Green
        Write-Host "URL: $tokenizerUrl" -ForegroundColor Cyan
        Write-Host ""
        
        # Save URL to file
        $tokenizerUrl | Out-File -FilePath "tokenizer_url.txt" -Encoding utf8
    } catch {
        Write-Host "✗ Failed to upload tokenizer file: $_" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Tokenizer file not found: $tokenizerFile" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload complete! URLs saved to:" -ForegroundColor Green
Write-Host "  - model_url.txt" -ForegroundColor Yellow
Write-Host "  - tokenizer_url.txt" -ForegroundColor Yellow
Write-Host ""
Write-Host "Update these in Render Environment Variables:" -ForegroundColor Cyan
Write-Host "  MODEL_PICKLE_URL=<model_url>" -ForegroundColor White
Write-Host "  TOKENIZER_PICKLE_URL=<tokenizer_url>" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

