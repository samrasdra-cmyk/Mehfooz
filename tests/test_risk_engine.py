from app.risk_engine import calculate_risk


def test_low_risk_baseline():
    result = calculate_risk(
        {"lake_area_km2": 1.0, "new_channels": False, "snowmelt_acceleration": "low"}
    )
    assert result["risk_score"] < 0.3
    assert result["is_critical"] is False


def test_high_risk_with_expansion_and_channels():
    result = calculate_risk(
        {"lake_area_km2": 2.5, "new_channels": True, "snowmelt_acceleration": "high"},
        historical_area=1.0,  # 2.5x expansion
    )
    assert result["risk_score"] > 0.65
    assert result["is_critical"] is True


def test_no_historical_area_defaults_expansion_to_one():
    result = calculate_risk(
        {"lake_area_km2": 5.0, "new_channels": False, "snowmelt_acceleration": "low"}
    )
    assert result["components"]["expansion_factor"] == 1.0


def test_risk_score_capped_at_one():
    result = calculate_risk(
        {"lake_area_km2": 100.0, "new_channels": True, "snowmelt_acceleration": "high"},
        historical_area=1.0,
    )
    assert result["risk_score"] <= 1.0
