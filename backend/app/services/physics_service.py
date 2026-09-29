"""
PetroNexus Physics-Informed Drilling Analytics Engine
Implements Teale's Mechanical Specific Energy (MSE), ECD margins,
and hydraulic boundary checks.

Teale's Equation (SI / Oilfield unified):
MSE = (WOB / A_bit) + (120 * pi * RPM * Torque) / (A_bit * ROP)
Where:
- WOB in kN (or tons converted to kN: 1 ton ~= 9.80665 kN)
- Torque in kN.m
- RPM in rev/min
- ROP in m/hr (converted to m/min)
- A_bit = pi * (d_bit / 2)^2
"""
import math
from typing import Optional, Dict, Any

def calculate_mse(
    wob_ton: float,
    torque_kn_m: float,
    rpm: float,
    rop_m_hr: float,
    bit_diameter_in: float = 8.5
) -> Optional[float]:
    """
    Calculates Mechanical Specific Energy (MSE) in MPa using Teale's equation.
    Returns None if any critical parameter is missing or <= 0.
    """
    if None in (wob_ton, torque_kn_m, rpm, rop_m_hr, bit_diameter_in):
        return None
    if wob_ton <= 0 or rop_m_hr <= 0 or rpm <= 0 or bit_diameter_in <= 0:
        return None

    # Convert bit diameter to meters
    d_bit_m = bit_diameter_in * 0.0254
    area_bit_m2 = math.pi * ((d_bit_m / 2.0) ** 2)

    # Convert WOB from metric tons to Newtons
    wob_n = wob_ton * 1000.0 * 9.80665

    # Axial component of MSE: WOB / Area (Pa)
    axial_pa = wob_n / area_bit_m2

    # Rotary component: (120 * pi * N * T) / (Area * ROP_m_min)
    # ROP in m/min = rop_m_hr / 60.0
    rop_m_min = rop_m_hr / 60.0
    torque_n_m = torque_kn_m * 1000.0

    rotary_pa = (2.0 * math.pi * rpm * torque_n_m) / (area_bit_m2 * rop_m_min)

    total_mse_pa = axial_pa + rotary_pa
    total_mse_mpa = total_mse_pa / 1e6

    return round(total_mse_mpa, 1)


def evaluate_drilling_physics(
    wob_ton: float,
    torque_kn_m: float,
    rpm: float,
    rop_m_hr: float,
    ecd_sg: float,
    mud_weight_sg: float,
    spp_psi: float,
    bit_diameter_in: float = 8.5
) -> Dict[str, Any]:
    """
    Evaluates drilling performance trends, MSE efficiency, and ECD margins.
    """
    mse = calculate_mse(wob_ton, torque_kn_m, rpm, rop_m_hr, bit_diameter_in)
    
    # ECD margin: difference between dynamic circulating density and static mud weight
    ecd_delta = round(ecd_sg - mud_weight_sg, 3) if (ecd_sg and mud_weight_sg) else 0.06

    # Qualitative MSE interpretation:
    # Typical baseline for shale/sandstone: 150-250 MPa.
    # Higher MSE (>350 MPa) indicates founder point, bit balling, or vibration.
    mse_status = "OPTIMAL"
    if mse is not None:
        if mse > 450:
            mse_status = "CRITICAL_INEFFICIENCY"
        elif mse > 320:
            mse_status = "ELEVATED_ENERGY"

    return {
        "mse_mpa": mse,
        "mse_status": mse_status,
        "ecd_delta_sg": ecd_delta,
        "ecd_margin_safe": ecd_delta <= 0.10,
        "bit_diameter_in": bit_diameter_in,
        "hydraulic_risk": "HIGH" if ecd_delta > 0.12 else "NORMAL"
    }
