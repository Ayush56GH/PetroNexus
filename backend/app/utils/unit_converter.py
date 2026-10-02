"""
PetroNexus Central Unit Conversion Utility
Standardizes all petroleum engineering and drilling parameters to canonical units:
- Depth: meters (m)
- Pressure: psi
- Torque: kN.m
- Flow rate: L/min (liters per minute)
- Mud Weight & ECD: SG (specific gravity)
- Weight & Hookload: metric tons (t) or klbf
- ROP: m/hr
- Temperature: Celsius (°C)
"""
from typing import Tuple, Dict, Any, Optional

CANONICAL_UNITS = {
    "depth": "m",
    "pressure": "psi",
    "torque": "kN.m",
    "flow_rate": "L/min",
    "mud_weight": "SG",
    "ecd": "SG",
    "wob": "ton",
    "hookload": "ton",
    "rop": "m/hr",
    "temperature": "C",
    "gas": "%"
}

class UnitConverter:

    @classmethod
    def convert(cls, value: float, unit: str, category: str) -> Tuple[float, str]:
        """Generic converter by dimension category"""
        cat = category.strip().lower()
        if cat in ["depth", "md", "tvd"]:
            return cls.normalize_depth(value, unit)
        elif cat in ["pressure", "spp"]:
            return cls.normalize_pressure(value, unit)
        elif cat in ["torque"]:
            return cls.normalize_torque(value, unit)
        elif cat in ["mud_weight", "ecd"]:
            return cls.normalize_mud_weight(value, unit)
        elif cat in ["flow", "flow_rate", "flow_in", "flow_out"]:
            return cls.normalize_flow_rate(value, unit)
        elif cat in ["wob", "hookload", "weight"]:
            return cls.normalize_weight(value, unit)
        elif cat in ["rop"]:
            return cls.normalize_rop(value, unit)
        elif cat in ["temperature", "temp"]:
            return cls.normalize_temperature(value, unit)
        return float(value), unit

    @staticmethod
    def normalize_depth(value: float, unit: str = "m") -> Tuple[float, str]:
        """Convert depth to meters (m)"""
        u = unit.strip().lower()
        if u in ["ft", "feet", "foot"]:
            return round(value * 0.3048, 2), "m"
        return round(float(value), 2), "m"

    @staticmethod
    def normalize_pressure(value: float, unit: str = "psi") -> Tuple[float, str]:
        """Convert pressure to psi"""
        u = unit.strip().lower()
        if u in ["bar"]:
            return round(value * 14.5038, 1), "psi"
        elif u in ["kpa"]:
            return round(value * 0.145038, 1), "psi"
        elif u in ["mpa"]:
            return round(value * 145.038, 1), "psi"
        return round(float(value), 1), "psi"

    @staticmethod
    def normalize_torque(value: float, unit: str = "kn.m") -> Tuple[float, str]:
        """Convert torque to kN.m"""
        u = unit.strip().lower().replace(" ", "").replace("_", "")
        if u in ["ft-lbf", "ftlbf", "ft.lbs", "ftlbs"]:
            return round(value * 0.001355818, 2), "kN.m"
        elif u in ["n.m", "nm"]:
            return round(value / 1000.0, 2), "kN.m"
        elif u in ["kft-lbf", "kftlbf"]:
            return round(value * 1.355818, 2), "kN.m"
        return round(float(value), 2), "kN.m"

    @staticmethod
    def normalize_flow_rate(value: float, unit: str = "l/min") -> Tuple[float, str]:
        """Convert flow rate to L/min"""
        u = unit.strip().lower().replace(" ", "")
        if u in ["gpm", "usgpm"]:
            return round(value * 3.78541, 1), "L/min"
        elif u in ["m3/hr", "m3/h"]:
            return round(value * 16.6667, 1), "L/min"
        elif u in ["bbl/min", "bpm"]:
            return round(value * 158.987, 1), "L/min"
        return round(float(value), 1), "L/min"

    @staticmethod
    def normalize_mud_weight(value: float, unit: str = "sg") -> Tuple[float, str]:
        """Convert mud weight or ECD to SG (specific gravity)"""
        u = unit.strip().lower().replace(" ", "")
        if u in ["ppg", "lb/gal"]:
            return round(value * 0.119826, 3), "SG"
        elif u in ["kg/m3", "kg/m^3"]:
            return round(value / 1000.0, 3), "SG"
        elif u in ["pcf", "lb/ft3"]:
            return round(value * 0.0160185, 3), "SG"
        return round(float(value), 3), "SG"

    @staticmethod
    def normalize_weight(value: float, unit: str = "ton") -> Tuple[float, str]:
        """Convert weight (WOB or Hookload) to metric tons (t)"""
        u = unit.strip().lower().replace(" ", "")
        if u in ["klbf", "kips"]:
            return round(value * 0.453592, 1), "ton"
        elif u in ["lbf", "lbs"]:
            return round(value * 0.000453592, 1), "ton"
        elif u in ["kn"]:
            return round(value * 0.101972, 1), "ton"
        return round(float(value), 1), "ton"

    @staticmethod
    def normalize_rop(value: float, unit: str = "m/hr") -> Tuple[float, str]:
        """Convert ROP to m/hr"""
        u = unit.strip().lower().replace(" ", "")
        if u in ["ft/hr", "fph"]:
            return round(value * 0.3048, 1), "m/hr"
        elif u in ["m/min"]:
            return round(value * 60.0, 1), "m/hr"
        elif u in ["ft/min"]:
            return round(value * 18.288, 1), "m/hr"
        return round(float(value), 1), "m/hr"

    @staticmethod
    def normalize_temperature(value: float, unit: str = "c") -> Tuple[float, str]:
        """Convert temperature to Celsius (°C)"""
        u = unit.strip().lower()
        if u in ["f", "fahrenheit", "degf"]:
            return round((value - 32.0) * 5.0 / 9.0, 1), "C"
        return round(float(value), 1), "C"

    @classmethod
    def convert_record(cls, record: Dict[str, Any], units_hint: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Takes a raw record dict and units mapping hint, converts fields to canonical units,
        and returns both normalized values and units metadata.
        """
        hints = units_hint or {}
        normalized = dict(record)
        original_units = {}
        normalized_units = {}

        converters = {
            "depth_md": (cls.normalize_depth, "depth"),
            "depth_tvd": (cls.normalize_depth, "depth"),
            "depth": (cls.normalize_depth, "depth"),
            "rop": (cls.normalize_rop, "rop"),
            "wob": (cls.normalize_weight, "wob"),
            "torque": (cls.normalize_torque, "torque"),
            "hookload": (cls.normalize_weight, "hookload"),
            "spp": (cls.normalize_pressure, "pressure"),
            "flow_in": (cls.normalize_flow_rate, "flow_rate"),
            "flow_out": (cls.normalize_flow_rate, "flow_rate"),
            "flow_rate": (cls.normalize_flow_rate, "flow_rate"),
            "ecd": (cls.normalize_mud_weight, "ecd"),
            "mud_weight": (cls.normalize_mud_weight, "mud_weight"),
            "temperature": (cls.normalize_temperature, "temperature"),
        }

        for field, (fn, dim) in converters.items():
            if field in record and record[field] is not None:
                try:
                    val = float(record[field])
                    raw_unit = hints.get(field, CANONICAL_UNITS.get(dim, ""))
                    norm_val, norm_unit = fn(val, raw_unit)
                    normalized[field] = norm_val
                    original_units[field] = raw_unit
                    normalized_units[field] = norm_unit
                except (ValueError, TypeError):
                    pass

        normalized["_original_units"] = original_units
        normalized["_normalized_units"] = normalized_units
        return normalized

unit_converter = UnitConverter()
