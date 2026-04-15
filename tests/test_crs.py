import pytest
from core.crs import resolve_crs

def test_resolve_epsg_string():
    crs = resolve_crs("EPSG:4326")
    assert crs.to_epsg() == 4326

def test_resolve_epsg_number_string():
    crs = resolve_crs("4326")
    assert crs.to_epsg() == 4326

def test_resolve_wgs84_alias():
    crs = resolve_crs("WGS84")
    assert crs.to_epsg() == 4326

def test_resolve_cgcs2000_english():
    crs = resolve_crs("CGCS2000")
    assert crs.to_epsg() == 4490

def test_resolve_cgcs2000_chinese():
    crs = resolve_crs("国家2000")
    assert crs.to_epsg() == 4490

def test_resolve_beijing54():
    crs = resolve_crs("北京54")
    assert crs.to_epsg() == 4214

def test_resolve_xian80():
    crs = resolve_crs("西安80")
    assert crs.to_epsg() == 4610

def test_resolve_unknown():
    with pytest.raises(ValueError, match="无法识别"):
        resolve_crs("火星坐标系XYZ")
