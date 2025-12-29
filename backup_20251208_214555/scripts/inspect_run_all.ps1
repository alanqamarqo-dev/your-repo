$path = Join-Path $PSScriptRoot '..\run_all.ps1' -Resolve
if (-not (Test-Path $path)) { Write-Error "run_all.ps1 not found at $path"; exit 1 }
# Print lines 1..200 with numbers
Get-Content $path | Select-Object -Index (0..199) | ForEach-Object -Begin { $i = 1 } -Process { "{0,4}: {1}" -f $i, $_; $i++ }

# Also output a small window around the integration block by searching for the marker
$lines = Get-Content $path
for ($ln=0; $ln -lt $lines.Length; $ln++) {
    if ($lines[$ln] -match 'Integration tests / system cohesion check') {
        $start = [math]::Max(0,$ln-10)
        $end = [math]::Min($lines.Length-1,$ln+40)
        Write-Output "\n--- Context around integration block (lines $($start+1)-$($end+1)) ---"
        for ($j=$start; $j -le $end; $j++) { "{0,4}: {1}" -f ($j+1), $lines[$j] }
        break
    }
}
