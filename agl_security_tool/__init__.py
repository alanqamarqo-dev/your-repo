"""
AGL Security — أداة تحليل أمان العقود الذكية
Smart Contract Security Analysis Tool

Usage:
    from agl_security_tool import AGLSecurityAudit
    audit = AGLSecurityAudit()
    result = audit.scan("path/to/contract.sol")
"""

__version__ = "1.1.0"
__author__ = "AGL Team"

from .core import AGLSecurityAudit
from .project_scanner import ProjectScanner

__all__ = ["AGLSecurityAudit", "ProjectScanner", "__version__"]
