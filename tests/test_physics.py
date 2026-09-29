"""
PetroNexus Physics-Informed Indicators & Trajectory Calculation Tests
Tests: Mechanical Specific Energy (MSE), ECD margin, Minimum Curvature Method, Unit conversions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.physics_service import calculate_mse, evaluate_drilling_physics
from backend.app.utils.trajectory_calc import calculate_trajectory, minimum_curvature
from backend.app.utils.units import feet_to_meters, meters_to_feet, ppg_to_sg

def test_mse_calculation():
    # Parameters: WOB = 12 tons, Torque = 16.8 kN.m, RPM = 110, ROP = 14.5 m/hr, Bit = 8.5 in
    mse = calculate_mse(wob_ton=12.0, torque_kn_m=16.8, rpm=110.0, rop_m_hr=14.5, bit_diameter_in=8.5)
    assert mse is not None
    assert 150.0 <= mse <= 2000.0 # Realistic physical range in MPa
    print(f"[PASS] test_mse_calculation passed (Calculated MSE: {mse} MPa).")

def test_physics_evaluation():
    eval_res = evaluate_drilling_physics(12.0, 16.8, 110.0, 14.5, 1.28, 1.22, 2450.0, 8.5)
    assert eval_res["mse_status"] in ["OPTIMAL", "ELEVATED_ENERGY", "CRITICAL_INEFFICIENCY"]
    assert eval_res["ecd_delta_sg"] == 0.06
    assert eval_res["ecd_margin_safe"] is True
    print("[PASS] test_physics_evaluation passed.")

def test_minimum_curvature_method():
    # Stations: 0m vertical to 100m inclined at 10 deg, 45 deg azimuth
    d_tvd, d_n, d_e, dls = minimum_curvature(0.0, 0.0, 0.0, 100.0, 10.0, 45.0)
    assert d_tvd > 98.0 # TVD slightly less than MD due to 10 deg build
    assert d_n > 0.0
    assert d_e > 0.0
    assert dls > 0.0

    stations = [
        {"md": 0.0, "inc": 0.0, "azi": 0.0},
        {"md": 500.0, "inc": 5.0, "azi": 45.0},
        {"md": 1000.0, "inc": 15.0, "azi": 50.0}
    ]
    traj = calculate_trajectory(stations, kb_elevation_m=112.5)
    assert len(traj) == 3
    assert traj[-1]["true_vertical_depth_m"] < 1000.0
    assert traj[-1]["tvdss_m"] < traj[-1]["true_vertical_depth_m"]
    print("[PASS] test_minimum_curvature_method passed.")

def test_unit_conversions():
    assert feet_to_meters(100.0) == 30.48
    assert meters_to_feet(30.48) == 100.0
    assert ppg_to_sg(10.0) == 1.198
    print("[PASS] test_unit_conversions passed.")

if __name__ == "__main__":
    test_mse_calculation()
    test_physics_evaluation()
    test_minimum_curvature_method()
    test_unit_conversions()
    print("All Physics and Engineering Math tests passed successfully!")
