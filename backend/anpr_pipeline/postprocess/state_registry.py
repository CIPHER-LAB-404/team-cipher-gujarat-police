"""
=============================================================================
Gujarat Police Sentinel - Centralized Indian State/UT Registration Registry
=============================================================================
Data-driven registry separating current active administrative jurisdictions
from historical and legacy codes, according to official MoRTH and CMVR rules.
=============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class StateRecord:
    """Represents an Indian State, Union Territory, or Special National Jurisdiction."""
    code: str
    name: str
    jurisdiction_type: str  # "STATE", "UNION_TERRITORY", "NATIONAL", "SPECIAL"
    active: bool = True
    is_legacy: bool = False
    replacement_code: Optional[str] = None
    legacy_codes: Tuple[str, ...] = ()
    min_rto_digits: int = 1
    max_rto_digits: int = 2
    notes: str = ""


# -----------------------------------------------------------------------------
# CURRENT ACTIVE JURISDICTIONS (28 States + 8 Union Territories)
# -----------------------------------------------------------------------------
CURRENT_STATES_DATA: Dict[str, StateRecord] = {
    # 28 States
    "AP": StateRecord("AP", "Andhra Pradesh", "STATE", active=True, legacy_codes=()),
    "AR": StateRecord("AR", "Arunachal Pradesh", "STATE", active=True, legacy_codes=()),
    "AS": StateRecord("AS", "Assam", "STATE", active=True, legacy_codes=()),
    "BR": StateRecord("BR", "Bihar", "STATE", active=True, legacy_codes=()),
    "CG": StateRecord("CG", "Chhattisgarh", "STATE", active=True, legacy_codes=()),
    "GA": StateRecord("GA", "Goa", "STATE", active=True, legacy_codes=()),
    "GJ": StateRecord("GJ", "Gujarat", "STATE", active=True, legacy_codes=()),
    "HR": StateRecord("HR", "Haryana", "STATE", active=True, legacy_codes=()),
    "HP": StateRecord("HP", "Himachal Pradesh", "STATE", active=True, legacy_codes=()),
    "JH": StateRecord("JH", "Jharkhand", "STATE", active=True, legacy_codes=()),
    "JK": StateRecord("JK", "Jammu & Kashmir", "STATE", active=True, legacy_codes=()),
    "KA": StateRecord("KA", "Karnataka", "STATE", active=True, legacy_codes=()),
    "KL": StateRecord("KL", "Kerala", "STATE", active=True, legacy_codes=()),
    "MP": StateRecord("MP", "Madhya Pradesh", "STATE", active=True, legacy_codes=()),
    "MH": StateRecord("MH", "Maharashtra", "STATE", active=True, legacy_codes=()),
    "MN": StateRecord("MN", "Manipur", "STATE", active=True, legacy_codes=()),
    "ML": StateRecord("ML", "Meghalaya", "STATE", active=True, legacy_codes=()),
    "MZ": StateRecord("MZ", "Mizoram", "STATE", active=True, legacy_codes=()),
    "NL": StateRecord("NL", "Nagaland", "STATE", active=True, legacy_codes=()),
    "OD": StateRecord("OD", "Odisha", "STATE", active=True, legacy_codes=("OR",), notes="Renamed from OR in 2012"),
    "PB": StateRecord("PB", "Punjab", "STATE", active=True, legacy_codes=()),
    "RJ": StateRecord("RJ", "Rajasthan", "STATE", active=True, legacy_codes=()),
    "SK": StateRecord("SK", "Sikkim", "STATE", active=True, legacy_codes=()),
    "TN": StateRecord("TN", "Tamil Nadu", "STATE", active=True, legacy_codes=()),
    "TS": StateRecord("TS", "Telangana", "STATE", active=True, legacy_codes=(), notes="Formed 2014 from AP"),
    "TR": StateRecord("TR", "Tripura", "STATE", active=True, legacy_codes=()),
    "UP": StateRecord("UP", "Uttar Pradesh", "STATE", active=True, legacy_codes=()),
    "UK": StateRecord("UK", "Uttarakhand", "STATE", active=True, legacy_codes=("UA",), notes="Renamed from UA in 2007"),
    "WB": StateRecord("WB", "West Bengal", "STATE", active=True, legacy_codes=()),

    # 8 Union Territories
    "AN": StateRecord("AN", "Andaman and Nicobar Islands", "UNION_TERRITORY", active=True),
    "CH": StateRecord("CH", "Chandigarh", "UNION_TERRITORY", active=True),
    "DH": StateRecord("DH", "Dadra and Nagar Haveli and Daman and Diu", "UNION_TERRITORY", active=True, legacy_codes=("DD", "DN"), notes="Merged in 2020"),
    "DL": StateRecord("DL", "Delhi", "UNION_TERRITORY", active=True, min_rto_digits=1, max_rto_digits=2, notes="Supports single-digit RTO (DL 1C, DL 3S, etc.)"),
    "LA": StateRecord("LA", "Ladakh", "UNION_TERRITORY", active=True, notes="Created 2019"),
    "LD": StateRecord("LD", "Lakshadweep", "UNION_TERRITORY", active=True),
    "PY": StateRecord("PY", "Puducherry", "UNION_TERRITORY", active=True),
    "JK_UT": StateRecord("JK", "Jammu and Kashmir (UT)", "UNION_TERRITORY", active=True),
}

# -----------------------------------------------------------------------------
# HISTORICAL / LEGACY JURISDICTIONS (Found in older / archival footage)
# -----------------------------------------------------------------------------
LEGACY_STATES_DATA: Dict[str, StateRecord] = {
    "UA": StateRecord("UA", "Uttaranchal (now Uttarakhand)", "STATE", active=False, is_legacy=True, replacement_code="UK", notes="Used until 2007"),
    "OR": StateRecord("OR", "Orissa (now Odisha)", "STATE", active=False, is_legacy=True, replacement_code="OD", notes="Used until 2012"),
    "DD": StateRecord("DD", "Daman and Diu", "UNION_TERRITORY", active=False, is_legacy=True, replacement_code="DH", notes="Merged into DH in 2020"),
    "DN": StateRecord("DN", "Dadra and Nagar Haveli", "UNION_TERRITORY", active=False, is_legacy=True, replacement_code="DH", notes="Merged into DH in 2020"),
}

# -----------------------------------------------------------------------------
# SPECIAL NATIONAL REGISTRATION MARKS
# -----------------------------------------------------------------------------
SPECIAL_JURISDICTIONS_DATA: Dict[str, StateRecord] = {
    "BH": StateRecord("BH", "Bharat Series (National)", "NATIONAL", active=True, notes="Pan-India non-state registration mark"),
    "DEF": StateRecord("DEF", "Ministry of Defence", "SPECIAL", active=True, notes="Military Armed Forces registrations"),
    "CD": StateRecord("CD", "Diplomatic Corps", "SPECIAL", active=True, notes="Corps Diplomatique (Embassies)"),
    "CC": StateRecord("CC", "Consular Corps", "SPECIAL", active=True, notes="Consular Corps (Consulates)"),
    "UN": StateRecord("UN", "United Nations", "SPECIAL", active=True, notes="United Nations personnel vehicles"),
}


class IndianStateRegistry:
    """Central access engine for Indian State/UT registration authority metadata."""

    CURRENT_CODES = {k: v for k, v in CURRENT_STATES_DATA.items() if k != "JK_UT"}
    LEGACY_CODES = dict(LEGACY_STATES_DATA)
    SPECIAL_CODES = dict(SPECIAL_JURISDICTIONS_DATA)

    # Fast lookup table: code -> StateRecord
    ALL_LOOKUP: Dict[str, StateRecord] = {}
    for _k, _v in CURRENT_CODES.items():
        ALL_LOOKUP[_k] = _v
    for _k, _v in LEGACY_CODES.items():
        ALL_LOOKUP[_k] = _v
    for _k, _v in SPECIAL_CODES.items():
        ALL_LOOKUP[_k] = _v

    @classmethod
    def get_state(cls, code: str) -> Optional[StateRecord]:
        """Returns the StateRecord for a 2-letter jurisdiction code, or None."""
        if not code:
            return None
        return cls.ALL_LOOKUP.get(code.upper().strip())

    @classmethod
    def is_current_state(cls, code: str) -> bool:
        """Returns True if code is an active current Indian State or UT."""
        return code.upper().strip() in cls.CURRENT_CODES

    @classmethod
    def is_legacy_state(cls, code: str) -> bool:
        """Returns True if code is an older legitimate historical code."""
        return code.upper().strip() in cls.LEGACY_CODES

    @classmethod
    def get_state_name(cls, code: str) -> str:
        """Returns human-readable jurisdiction name."""
        rec = cls.get_state(code)
        if rec:
            return rec.name
        return "Unknown Jurisdiction"

    @classmethod
    def get_replacement_code(cls, code: str) -> Optional[str]:
        """Returns modern code if the given code is legacy (e.g. UA -> UK)."""
        rec = cls.LEGACY_CODES.get(code.upper().strip())
        return rec.replacement_code if rec else None


# Convenience instance
STATE_REGISTRY = IndianStateRegistry
