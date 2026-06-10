"""Engineering reporting package."""
from app.services.agentic.reporting.schemas import EngineeringReport, ReporterResult

__all__ = ["EngineeringReport", "ReporterResult"]


def generate_engineering_report(*args, **kwargs):
    from app.services.agentic.reporting.report_generator import generate_engineering_report as _gen

    return _gen(*args, **kwargs)
