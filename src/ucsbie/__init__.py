"""ucsbie — UCSB Innovation & Entrepreneurship data CLI/library.

Public-data harvester for UCSB technologies available for licensing
(UCOP techtransfer portal) and UCSB ventures (TIA Startup Database).
"""
from .cli import (  # noqa: F401
    make_session,
    fetch_tech_list,
    fetch_tech_detail,
    fetch_categories,
    fetch_startups,
    main,
)

__version__ = "0.1.0"
