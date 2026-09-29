"""
PetroNexus Engineering Unit Normalization Utility
Provides transparent conversions between oilfield imperial and SI/metric units
without silently modifying ambiguous values.
"""

def feet_to_meters(ft: float) -> float:
    return round(ft * 0.3048, 2)

def meters_to_feet(m: float) -> float:
    return round(m / 0.3048, 2)

def psi_to_bar(psi: float) -> float:
    return round(psi * 0.0689476, 2)

def bar_to_psi(bar: float) -> float:
    return round(bar / 0.0689476, 2)

def ppg_to_sg(ppg: float) -> float:
    # 1 ppg = 0.119826 SG
    return round(ppg * 0.119826, 3)

def sg_to_ppg(sg: float) -> float:
    return round(sg / 0.119826, 2)

def gpm_to_lpm(gpm: float) -> float:
    return round(gpm * 3.78541, 1)

def lpm_to_gpm(lpm: float) -> float:
    return round(lpm / 3.78541, 1)

def normalize_drilling_units(data: dict) -> dict:
    """
    Normalizes input dictionaries to PetroNexus metric standards:
    - Depth: meters (m)
    - Mud weight / ECD: specific gravity (SG)
    - Flow rate: liters/min (L/min)
    - Pressure: psi (display standard in OIL eRTMAC)
    - Torque: kN.m
    - WOB: metric tons
    """
    normalized = {}
    for k, v in data.items():
        if v is None:
            normalized[k] = None
            continue
        try:
            val = float(v)
        except (ValueError, TypeError):
            normalized[k] = v
            continue

        key_lower = k.lower()
        if "ft" in key_lower or "feet" in key_lower:
            normalized[k + "_normalized_m"] = feet_to_meters(val)
        elif "ppg" in key_lower:
            normalized[k + "_normalized_sg"] = ppg_to_sg(val)
        elif "gpm" in key_lower:
            normalized[k + "_normalized_lpm"] = gpm_to_lpm(val)
        else:
            normalized[k] = val
            
    return normalized
