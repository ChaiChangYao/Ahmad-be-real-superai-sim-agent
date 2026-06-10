"""Reporting layer errors."""
from __future__ import annotations


class ReportGenerationError(Exception):
    def __init__(self, message: str, *, code: str = "report_generation_failed", details: str = ""):
        super().__init__(message)
        self.code = code
        self.details = details
