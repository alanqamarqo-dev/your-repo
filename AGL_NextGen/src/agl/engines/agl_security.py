#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGL Security Suite - نقطة الدخول الموحدة
==========================================

يوفر واجهة واحدة سهلة لتحليل أمان العقود الذكية

الاستخدام:
    # CLI
    python agl_security.py scan contract.sol
    python agl_security.py scan ./contracts/ --output report.json
    python agl_security.py scan contract.sol --format markdown

    # Python API
    from agl_security import scan_contract, scan_directory
    findings = scan_contract("contract.sol")

Author: AGL Team
Date: 2026-02-04
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# إضافة المسار
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# استيراد المحللات
from smart_contract_analyzer import SmartContractAnalyzer, analyze_contract


class AGLSecuritySuite:
    """
    مجموعة أدوات التحليل الأمني الموحدة
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, config: Optional[Dict] = None):
        """
        تهيئة المجموعة
        
        Args:
            config: إعدادات اختيارية
        """
        self.config = config or {}
        self.analyzer = SmartContractAnalyzer()
        
        # إعدادات افتراضية
        self.severity_filter = self.config.get('severity_filter', ['critical', 'high', 'medium', 'low'])
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        
        # محاولة تحميل الأدوات الخارجية
        self._check_external_tools()
    
    def _check_external_tools(self):
        """التحقق من الأدوات الخارجية"""
        self.tools_available = {
            'slither': self._check_tool('slither', ['slither', '--version']),
            'mythril': self._check_tool('mythril', ['myth', 'version']),
            'semgrep': self._check_tool('semgrep', ['semgrep', '--version']),
        }
    
    def _check_tool(self, name: str, cmd: list) -> bool:
        """التحقق من وجود أداة"""
        try:
            import subprocess
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        فحص ملف Solidity
        
        Args:
            file_path: مسار الملف
            
        Returns:
            نتائج الفحص
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.sol':
            raise ValueError(f"Not a Solidity file: {file_path}")
        
        # قراءة الكود
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
        
        # التحليل الأساسي
        result = self.analyzer.analyze(source_code)
        
        # إضافة معلومات الملف
        result['file'] = str(file_path)
        result['file_name'] = file_path.name
        result['scan_time'] = datetime.now().isoformat()
        
        # فلترة النتائج
        result['findings'] = self._filter_findings(result['findings'])
        
        # محاولة استخدام Slither إن وُجد
        if self.tools_available.get('slither'):
            try:
                slither_findings = self._run_slither(str(file_path))
                result['findings'].extend(slither_findings)
                result['tools_used'] = result.get('tools_used', ['agl']) + ['slither']
            except Exception as e:
                result['warnings'] = result.get('warnings', []) + [f"Slither error: {e}"]
        
        # إزالة التكرارات
        result['findings'] = self._deduplicate(result['findings'])
        
        # ترتيب حسب الخطورة
        result['findings'] = self._sort_findings(result['findings'])
        
        return result
    
    def scan_directory(self, dir_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        فحص مجلد كامل
        
        Args:
            dir_path: مسار المجلد
            recursive: فحص المجلدات الفرعية
            
        Returns:
            نتائج الفحص
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        # البحث عن ملفات Solidity
        pattern = "**/*.sol" if recursive else "*.sol"
        sol_files = list(dir_path.glob(pattern))
        
        if not sol_files:
            return {
                'error': f"No Solidity files found in {dir_path}",
                'findings': [],
            }
        
        # فحص كل ملف
        all_results = {
            'scan_time': datetime.now().isoformat(),
            'directory': str(dir_path),
            'files_scanned': len(sol_files),
            'files': {},
            'summary': {
                'total_findings': 0,
                'by_severity': {},
                'by_category': {},
            }
        }
        
        for sol_file in sol_files:
            try:
                result = self.scan_file(str(sol_file))
                all_results['files'][str(sol_file)] = result
                
                # تحديث الملخص
                for finding in result.get('findings', []):
                    all_results['summary']['total_findings'] += 1
                    
                    sev = finding.get('severity', 'unknown')
                    all_results['summary']['by_severity'][sev] = \
                        all_results['summary']['by_severity'].get(sev, 0) + 1
                    
                    cat = finding.get('category', 'unknown')
                    all_results['summary']['by_category'][cat] = \
                        all_results['summary']['by_category'].get(cat, 0) + 1
                        
            except Exception as e:
                all_results['files'][str(sol_file)] = {
                    'error': str(e),
                    'findings': [],
                }
        
        return all_results
    
    def _filter_findings(self, findings: List[Dict]) -> List[Dict]:
        """فلترة النتائج"""
        filtered = []
        for f in findings:
            if f.get('severity') in self.severity_filter:
                if f.get('confidence', 1.0) >= self.confidence_threshold:
                    filtered.append(f)
        return filtered
    
    def _deduplicate(self, findings: List[Dict]) -> List[Dict]:
        """إزالة التكرارات"""
        seen = set()
        unique = []
        
        for f in findings:
            key = (f.get('line'), f.get('category'), f.get('title', '')[:20])
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique
    
    def _sort_findings(self, findings: List[Dict]) -> List[Dict]:
        """ترتيب حسب الخطورة"""
        order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        return sorted(findings, key=lambda x: order.get(x.get('severity', 'info'), 5))
    
    def _run_slither(self, file_path: str) -> List[Dict]:
        """تشغيل Slither"""
        import subprocess
        
        cmd = ['slither', file_path, '--json', '-']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            return []
        
        try:
            data = json.loads(result.stdout)
            findings = []
            
            for det in data.get('results', {}).get('detectors', []):
                severity_map = {
                    'High': 'high',
                    'Medium': 'medium',
                    'Low': 'low',
                    'Informational': 'info',
                }
                
                elements = det.get('elements', [])
                line = 0
                if elements:
                    lines = elements[0].get('source_mapping', {}).get('lines', [])
                    line = min(lines) if lines else 0
                
                findings.append({
                    'id': f"SLITHER-{det.get('check', 'UNKNOWN')}",
                    'title': det.get('check', 'Unknown'),
                    'severity': severity_map.get(det.get('impact', 'Low'), 'low'),
                    'category': det.get('check', 'other'),
                    'line': line,
                    'description': det.get('description', ''),
                    'confidence': 0.85,
                    'source': 'slither',
                })
            
            return findings
        except:
            return []
    
    def generate_report(self, results: Dict, output_path: str, format: str = 'json'):
        """
        توليد تقرير
        
        Args:
            results: نتائج الفحص
            output_path: مسار الملف
            format: تنسيق التقرير (json, markdown, html)
        """
        if format == 'json':
            self._write_json_report(results, output_path)
        elif format == 'markdown':
            self._write_markdown_report(results, output_path)
        else:
            self._write_json_report(results, output_path)
    
    def _write_json_report(self, results: Dict, output_path: str):
        """كتابة تقرير JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"📊 Report saved: {output_path}")
    
    def _write_markdown_report(self, results: Dict, output_path: str):
        """كتابة تقرير Markdown"""
        lines = [
            "# 🛡️ AGL Security Audit Report",
            "",
            f"**Generated:** {results.get('scan_time', 'Unknown')}",
            "",
        ]
        
        # إذا كان فحص ملف واحد
        if 'file' in results:
            lines.append(f"**File:** `{results['file']}`")
            lines.append("")
            lines.append(f"**Findings:** {len(results.get('findings', []))}")
            lines.append("")
            
            self._add_findings_to_markdown(lines, results.get('findings', []))
        
        # إذا كان فحص مجلد
        elif 'files' in results:
            lines.append(f"**Directory:** `{results.get('directory')}`")
            lines.append(f"**Files Scanned:** {results.get('files_scanned', 0)}")
            lines.append("")
            
            summary = results.get('summary', {})
            lines.append("## Summary")
            lines.append("")
            lines.append(f"- **Total Findings:** {summary.get('total_findings', 0)}")
            
            by_sev = summary.get('by_severity', {})
            for sev in ['critical', 'high', 'medium', 'low', 'info']:
                count = by_sev.get(sev, 0)
                if count > 0:
                    lines.append(f"- **{sev.upper()}:** {count}")
            lines.append("")
            
            # النتائج لكل ملف
            for file_path, file_results in results.get('files', {}).items():
                findings = file_results.get('findings', [])
                if findings:
                    lines.append(f"## 📄 {Path(file_path).name}")
                    lines.append("")
                    self._add_findings_to_markdown(lines, findings)
        
        # كتابة الملف
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"📊 Report saved: {output_path}")
    
    def _add_findings_to_markdown(self, lines: List[str], findings: List[Dict]):
        """إضافة النتائج للـ Markdown"""
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'info': 'ℹ️',
        }
        
        for f in findings:
            sev = f.get('severity', 'info')
            emoji = severity_emoji.get(sev, '⚪')
            
            lines.append(f"### {emoji} [{sev.upper()}] {f.get('title', 'Unknown')}")
            lines.append("")
            lines.append(f"- **ID:** `{f.get('id', 'N/A')}`")
            lines.append(f"- **Line:** {f.get('line', 'N/A')}")
            lines.append(f"- **Category:** {f.get('category', 'N/A')}")
            lines.append(f"- **Confidence:** {f.get('confidence', 0):.0%}")
            lines.append("")
            lines.append(f"> {f.get('description', 'No description')}")
            lines.append("")
            lines.append("---")
            lines.append("")


# ============================================================================
# API Functions
# ============================================================================

def scan_contract(file_path: str, **kwargs) -> Dict[str, Any]:
    """
    فحص عقد ذكي
    
    Args:
        file_path: مسار الملف
        **kwargs: إعدادات إضافية
        
    Returns:
        نتائج الفحص
    """
    suite = AGLSecuritySuite(kwargs)
    return suite.scan_file(file_path)


def scan_directory(dir_path: str, **kwargs) -> Dict[str, Any]:
    """
    فحص مجلد عقود
    
    Args:
        dir_path: مسار المجلد
        **kwargs: إعدادات إضافية
        
    Returns:
        نتائج الفحص
    """
    suite = AGLSecuritySuite(kwargs)
    return suite.scan_directory(dir_path, recursive=kwargs.get('recursive', True))


# ============================================================================
# CLI
# ============================================================================

def print_banner():
    """طباعة البانر"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   █████╗  ██████╗ ██╗         ███████╗███████╗ ██████╗       ║
║  ██╔══██╗██╔════╝ ██║         ██╔════╝██╔════╝██╔════╝       ║
║  ███████║██║  ███╗██║         ███████╗█████╗  ██║            ║
║  ██╔══██║██║   ██║██║         ╚════██║██╔══╝  ██║            ║
║  ██║  ██║╚██████╔╝███████╗    ███████║███████╗╚██████╗       ║
║  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚══════╝╚══════╝ ╚═════╝       ║
║                                                               ║
║         🛡️  Smart Contract Security Analyzer                  ║
║                    Version 1.0.0                              ║
╚═══════════════════════════════════════════════════════════════╝
""")


def print_results(results: Dict, verbose: bool = False):
    """طباعة النتائج"""
    severity_emoji = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'info': 'ℹ️',
    }
    
    # فحص ملف واحد
    if 'file' in results:
        findings = results.get('findings', [])
        print(f"\n📄 File: {results['file']}")
        print(f"📊 Findings: {len(findings)}")
        print("-" * 50)
        
        for f in findings:
            sev = f.get('severity', 'info')
            emoji = severity_emoji.get(sev, '⚪')
            print(f"\n{emoji} [{sev.upper()}] {f.get('title')}")
            print(f"   Line: {f.get('line')}")
            print(f"   {f.get('description')}")
    
    # فحص مجلد
    elif 'files' in results:
        summary = results.get('summary', {})
        print(f"\n📁 Directory: {results.get('directory')}")
        print(f"📄 Files scanned: {results.get('files_scanned')}")
        print(f"🔍 Total findings: {summary.get('total_findings', 0)}")
        print("-" * 50)
        
        by_sev = summary.get('by_severity', {})
        for sev in ['critical', 'high', 'medium', 'low', 'info']:
            count = by_sev.get(sev, 0)
            if count > 0:
                emoji = severity_emoji.get(sev, '⚪')
                bar = '█' * min(count, 20)
                print(f"   {emoji} {sev.upper():10} {count:3} {bar}")
        
        if verbose:
            print("\n" + "=" * 50)
            for file_path, file_results in results.get('files', {}).items():
                findings = file_results.get('findings', [])
                if findings:
                    print(f"\n📄 {Path(file_path).name}")
                    for f in findings:
                        sev = f.get('severity', 'info')
                        emoji = severity_emoji.get(sev, '⚪')
                        print(f"   {emoji} Line {f.get('line')}: {f.get('title')}")


def main():
    """نقطة الدخول الرئيسية"""
    parser = argparse.ArgumentParser(
        description="AGL Security Suite - Smart Contract Security Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agl_security.py scan contract.sol
  python agl_security.py scan ./contracts/ --output report.json
  python agl_security.py scan contract.sol --format markdown --output report.md
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a file or directory')
    scan_parser.add_argument('target', help='File or directory to scan')
    scan_parser.add_argument('--output', '-o', help='Output file for report')
    scan_parser.add_argument('--format', '-f', choices=['json', 'markdown'], default='json',
                            help='Report format')
    scan_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    scan_parser.add_argument('--severity', '-s', nargs='+', 
                            default=['critical', 'high', 'medium', 'low'],
                            help='Severity levels to report')
    scan_parser.add_argument('--confidence', '-c', type=float, default=0.5,
                            help='Minimum confidence threshold (0.0-1.0)')
    
    args = parser.parse_args()
    
    if not args.command:
        print_banner()
        parser.print_help()
        return 0
    
    if args.command == 'scan':
        print_banner()
        
        target = Path(args.target)
        
        config = {
            'severity_filter': args.severity,
            'confidence_threshold': args.confidence,
        }
        
        suite = AGLSecuritySuite(config)
        
        try:
            if target.is_file():
                results = suite.scan_file(str(target))
            else:
                results = suite.scan_directory(str(target))
            
            # طباعة النتائج
            print_results(results, args.verbose)
            
            # حفظ التقرير
            if args.output:
                suite.generate_report(results, args.output, args.format)
            
            # Return code based on findings
            findings = results.get('findings', [])
            if not findings and 'summary' in results:
                findings = [None] * results['summary'].get('total_findings', 0)
            
            critical_high = sum(1 for f in results.get('findings', []) 
                              if f and f.get('severity') in ['critical', 'high'])
            return 1 if critical_high > 0 else 0
            
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
