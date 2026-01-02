import subprocess


def capture_screenshot():
    cmd = [
        'powershell',
        '-NoProfile',
        '-Command',
        (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "Add-Type -AssemblyName System.Drawing; "
            "$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, "
            "[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); "
            "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
            "$graphics.CopyFromScreen(0, 0, 0, 0, $bmp.Size); "
            "$bmp.Save(\"vision_capture.png\");"
        )
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print('Screenshot captured successfully via Native PowerShell')
    else:
        print('Screenshot command failed:')
        print(result.stderr.strip())


if __name__ == "__main__":
    capture_screenshot()
