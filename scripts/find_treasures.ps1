
$activePath = "D:\AGL"
$backupPath = "D:\AGL\backups"
$reportPath = "D:\AGL\HIDDEN_TREASURES_REPORT.md"

# 1. Build Index of Active Files (Name -> Length)
Write-Host "Building Active File Index..."
$activeFiles = @{}
Get-ChildItem -Path $activePath -Recurse -File -Filter *.py | 
    Where-Object { $_.FullName -notmatch "\\backups\\" -and $_.FullName -notmatch "\\.venv\\" } | 
    ForEach-Object { $activeFiles[$_.Name] = $_.Length }

# 2. Scan Backups for Treasures
Write-Host "Scanning Backups for Lost Treasures..."
$treasures = @()

# Focus on repo-copy-HILT-experiment and other top-level backups first to save time
$backupFiles = Get-ChildItem -Path $backupPath -Recurse -File -Filter *.py | 
    Where-Object { $_.FullName -notmatch "\\.venv\\" -and $_.FullName -notmatch "\\site-packages\\" }

foreach ($file in $backupFiles) {
    $status = ""
    $reason = ""
    
    # Check 1: Is it unique?
    if (-not $activeFiles.ContainsKey($file.Name)) {
        $status = "💎 UNIQUE"
        $reason = "Found only in backups"
    }
    # Check 2: Is it significantly larger?
    elseif ($file.Length -gt ($activeFiles[$file.Name] * 1.2)) {
        $status = "💪 STRONGER"
        $diff = [math]::Round(($file.Length - $activeFiles[$file.Name]) / 1024, 2)
        $reason = "Backup is larger by $diff KB"
    }
    
    # Check 3: Special Keywords in Name
    if ($file.Name -match "Omega|Genesis|Secret|Hidden|Advanced|Heikal|Quantum|Consciousness") {
        if ($status -eq "") { $status = "✨ INTERESTING" }
        $reason += " (Contains Power Keyword)"
    }

    if ($status -ne "") {
        $treasures += [PSCustomObject]@{
            Name = $file.Name
            Status = $status
            Reason = $reason
            Path = $file.FullName
            SizeKB = [math]::Round($file.Length / 1024, 2)
        }
    }
}

# 3. Generate Report
Write-Host "Generating Report..."
$reportContent = "# AGL Hidden Treasures Report`n`n"
$reportContent += "Generated on: $(Get-Date)`n"
$reportContent += "Total Treasures Found: $($treasures.Count)`n`n"

$reportContent += "## 💎 Unique Files (Found ONLY in Backups)`n"
$reportContent += "| File Name | Size (KB) | Location |`n"
$reportContent += "|---|---|---|`n"
$treasures | Where-Object { $_.Status -eq "💎 UNIQUE" } | Sort-Object SizeKB -Descending | Select-Object -First 50 | ForEach-Object {
    $relPath = $_.Path.Replace($backupPath, "backups")
    $reportContent += "| **$($_.Name)** | $($_.SizeKB) | `$relPath` |`n"
}

$reportContent += "`n## 💪 Stronger Versions (Backup is Larger)`n"
$reportContent += "| File Name | Size (KB) | Reason | Location |`n"
$reportContent += "|---|---|---|---|`n"
$treasures | Where-Object { $_.Status -eq "💪 STRONGER" } | Sort-Object SizeKB -Descending | Select-Object -First 50 | ForEach-Object {
    $relPath = $_.Path.Replace($backupPath, "backups")
    $reportContent += "| **$($_.Name)** | $($_.SizeKB) | $($_.Reason) | `$relPath` |`n"
}

$reportContent | Out-File -FilePath $reportPath -Encoding utf8
Write-Host "Done! Report saved to $reportPath"
