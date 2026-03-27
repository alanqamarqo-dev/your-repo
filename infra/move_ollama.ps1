# Script to move Ollama models to D: drive to save space on C:

$Source = "$env:USERPROFILE\.ollama\models"
$Dest = "D:\OllamaModels"

Write-Host "Stopping Ollama..." -ForegroundColor Yellow
Stop-Process -Name "ollama_app" -ErrorAction SilentlyContinue
Stop-Process -Name "ollama" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

if (-not (Test-Path $Dest)) {
    Write-Host "Creating destination directory: $Dest" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $Dest | Out-Null
}

if (Test-Path $Source) {
    Write-Host "Moving models from $Source to $Dest..." -ForegroundColor Cyan
    # Use Robocopy for robust moving
    robocopy $Source $Dest /E /MOVE /IS /IT
    
    if ($LASTEXITCODE -lt 8) {
        Write-Host "Move complete." -ForegroundColor Green
    } else {
        Write-Host "Error moving files. Robocopy exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} else {
    Write-Host "Source directory not found or already moved." -ForegroundColor Yellow
}

# Set Environment Variable permanently
Write-Host "Setting OLLAMA_MODELS environment variable..." -ForegroundColor Cyan
[System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $Dest, 'User')

Write-Host "Environment variable set. Please restart your terminal and Ollama." -ForegroundColor Green
Write-Host "You can restart Ollama now." -ForegroundColor Green
