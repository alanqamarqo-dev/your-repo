#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تقرير شامل لاستهلاك الذاكرة (RAM) - جميع العمليات
"""

import psutil
import os

print("\n" + "="*80)
print("📊 تقرير شامل لاستهلاك الذاكرة (RAM) - جميع العمليات")
print("="*80 + "\n")

# معلومات الذاكرة العامة
memory = psutil.virtual_memory()
total_gb = memory.total / (1024**3)
used_gb = memory.used / (1024**3)
free_gb = memory.available / (1024**3)
percent = memory.percent

print("📈 حالة الذاكرة:")
print(f"   إجمالي الذاكرة: {total_gb:.2f} GB")
print(f"   الذاكرة المستخدمة: {used_gb:.2f} GB ({percent:.1f}%) " + ("🔴 حرج!" if percent > 80 else "⚠️ عالي" if percent > 60 else "✅ جيد"))
print(f"   الذاكرة المتاحة: {free_gb:.2f} GB")
print("\n" + "-"*80 + "\n")

# جمع بيانات جميع العمليات
processes = []
for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
    try:
        mb = proc.memory_info().rss / (1024**2)
        if mb > 50:  # العمليات التي تستهلك أكثر من 50 MB فقط
            processes.append({
                'name': proc.name(),
                'mb': mb,
                'pid': proc.pid
            })
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

# ترتيب العمليات
processes.sort(key=lambda x: x['mb'], reverse=True)

# تصنيف العمليات
print("🔴 العمليات الثقيلة جداً (أكثر من 500 MB):\n")
heavy = [p for p in processes if p['mb'] > 500]
if heavy:
    for proc in heavy:
        print(f"   {proc['name']:<30} {proc['mb']:>8.1f} MB  [PID: {proc['pid']}]")
else:
    print("   لا توجد عمليات\n")

print("\n" + "-"*80 + "\n")
print("🟠 العمليات الثقيلة (300-500 MB):\n")
medium_heavy = [p for p in processes if 300 <= p['mb'] <= 500]
if medium_heavy:
    for proc in medium_heavy:
        print(f"   {proc['name']:<30} {proc['mb']:>8.1f} MB  [PID: {proc['pid']}]")
else:
    print("   لا توجد عمليات\n")

print("\n" + "-"*80 + "\n")
print("🟡 العمليات العادية (100-300 MB):\n")
medium = [p for p in processes if 100 <= p['mb'] < 300]
if medium:
    for proc in medium[:15]:  # أول 15 فقط
        print(f"   {proc['name']:<30} {proc['mb']:>8.1f} MB  [PID: {proc['pid']}]")
    if len(medium) > 15:
        print(f"   ... وعدد {len(medium) - 15} عملية أخرى")
else:
    print("   لا توجد عمليات\n")

print("\n" + "="*80)
print(f"📋 إجمالي العمليات التي تستهلك أكثر من 50 MB: {len(processes)}")
print(f"📊 إجمالي استهلاكها: {sum(p['mb'] for p in processes):.2f} MB")
print("="*80 + "\n")

# التوصيات
print("💡 التوصيات:")
if percent > 80:
    print("   🔴 استهلاك الذاكرة حرج جداً (>80%)")
    print("      ينصح بإيقاف بعض العمليات الثقيلة")
    print("      العمليات الموصى بإيقافها:")
    for proc in heavy[:3]:
        print(f"         - {proc['name']}")
elif percent > 60:
    print("   ⚠️ استهلاك الذاكرة عالي (60-80%)")
    print("      قد تواجه تأخير في الأداء")
else:
    print("   ✅ استهلاك الذاكرة طبيعي")
    print("      الأداء جيد")

print()
