#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تقرير شامل لاستهلاك الذاكرة (RAM) - جميع العمليات
"""

import subprocess

print("\n" + "="*90)
print("📊 تقرير شامل لاستهلاك الذاكرة (RAM) - جميع العمليات")
print("="*90 + "\n")

# الحصول على معلومات الذاكرة باستخدام PowerShell
ps_cmd = """
$OS = Get-CimInstance Win32_OperatingSystem
$total = [math]::Round($OS.TotalVisibleMemorySize / 1MB, 2)
$free = [math]::Round($OS.FreePhysicalMemory / 1MB, 2)
$used = $total - $free
$percent = [math]::Round(($used / $total) * 100, 1)

Write-Host "TOTAL:$total"
Write-Host "USED:$used"
Write-Host "FREE:$free"
Write-Host "PERCENT:$percent"
"""

try:
    result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=5)
    lines = result.stdout.strip().split('\n')
    
    for line in lines:
        if line.startswith('TOTAL:'):
            total = float(line.split(':')[1])
        elif line.startswith('USED:'):
            used = float(line.split(':')[1])
        elif line.startswith('FREE:'):
            free = float(line.split(':')[1])
        elif line.startswith('PERCENT:'):
            percent = float(line.split(':')[1])
    
    print("📈 حالة الذاكرة:")
    print(f"   إجمالي الذاكرة: {total:.2f} GB")
    print(f"   الذاكرة المستخدمة: {used:.2f} GB ({percent:.1f}%) ", end="")
    if percent > 80:
        print("🔴 حرج!")
    elif percent > 60:
        print("⚠️ عالي")
    else:
        print("✅ جيد")
    print(f"   الذاكرة المتاحة: {free:.2f} GB")
    
except:
    print("⚠️ خطأ في الحصول على معلومات الذاكرة")

print("\n" + "-"*90 + "\n")

# الحصول على العمليات الثقيلة
ps_procs = """
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 50 Name, @{Label='MB'; Expression={[math]::Round($_.WorkingSet / 1MB, 1)}} | ConvertTo-Csv -NoTypeInformation
"""

try:
    result = subprocess.run(['powershell', '-Command', ps_procs], capture_output=True, text=True, timeout=10)
    lines = result.stdout.strip().split('\n')
    
    # قراءة البيانات
    processes = []
    header = None
    
    for i, line in enumerate(lines):
        if i == 0:
            header = line
            continue
        parts = line.split(',')
        if len(parts) >= 2:
            name = parts[0].strip('"')
            mb_str = parts[1].strip('"')
            try:
                mb = float(mb_str)
                if mb > 50:  # العمليات التي تستهلك أكثر من 50 MB
                    processes.append({'name': name, 'mb': mb})
            except:
                pass
    
    # ترتيب وتصنيف
    processes.sort(key=lambda x: x['mb'], reverse=True)
    
    print("🔴 العمليات الثقيلة جداً (أكثر من 500 MB):\n")
    heavy = [p for p in processes if p['mb'] > 500]
    if heavy:
        for proc in heavy:
            print(f"   {proc['name']:<40} {proc['mb']:>8.1f} MB")
    else:
        print("   لا توجد عمليات\n")
    
    print("\n" + "-"*90 + "\n")
    print("🟠 العمليات الثقيلة (300-500 MB):\n")
    medium_heavy = [p for p in processes if 300 <= p['mb'] <= 500]
    if medium_heavy:
        for proc in medium_heavy:
            print(f"   {proc['name']:<40} {proc['mb']:>8.1f} MB")
    else:
        print("   لا توجد عمليات\n")
    
    print("\n" + "-"*90 + "\n")
    print("🟡 العمليات العادية (100-300 MB):\n")
    medium = [p for p in processes if 100 <= p['mb'] < 300]
    if medium:
        for proc in medium[:20]:  # أول 20 عملية
            print(f"   {proc['name']:<40} {proc['mb']:>8.1f} MB")
        if len(medium) > 20:
            print(f"\n   ... و {len(medium) - 20} عملية أخرى")
    else:
        print("   لا توجد عمليات\n")
    
    print("\n" + "="*90)
    total_consumed = sum(p['mb'] for p in processes)
    print(f"📋 إجمالي العمليات (أكثر من 50 MB): {len(processes)}")
    print(f"📊 إجمالي استهلاكها: {total_consumed:.2f} MB")
    print("="*90 + "\n")
    
except Exception as e:
    print(f"⚠️ خطأ: {e}")
