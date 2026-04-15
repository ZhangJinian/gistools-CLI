import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString
from pathlib import Path
from core.spatial import buffer_file


@pytest.fixture
def point_geojson(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    )
    p = tmp_path / "points.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p


@pytest.fixture
def line_geojson(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[LineString([(114.0, 22.5), (114.1, 22.6)])],
        crs="EPSG:4326",
    )
    p = tmp_path / "line.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p


def test_buffer_points_meters(point_geojson, tmp_path):
    dst = tmp_path / "out.geojson"
    buffer_file(point_geojson, dst, distance=500, unit="meters", dissolve=False)
    result = gpd.read_file(str(dst))
    assert len(result) == 2
    assert result.geometry.geom_type.iloc[0] == "Polygon"


def test_buffer_line_km(line_geojson, tmp_path):
    dst = tmp_path / "out.geojson"
    buffer_file(line_geojson, dst, distance=1, unit="km", dissolve=False)
    result = gpd.read_file(str(dst))
    assert len(result) == 1
    assert result.geometry.geom_type.iloc[0] == "Polygon"


def test_buffer_dissolve(point_geojson, tmp_path):
    dst = tmp_path / "out.geojson"
    buffer_file(point_geojson, dst, distance=100000, unit="meters", dissolve=True)
    result = gpd.read_file(str(dst))
    assert len(result) == 1


def test_buffer_empty_input(tmp_path):
    """0 个要素 → 输出空文件，不报错"""
    gdf = gpd.GeoDataFrame({"id": []}, geometry=[], crs="EPSG:4326")
    src = tmp_path / "empty.geojson"
    gdf.to_file(str(src), driver="GeoJSON")
    dst = tmp_path / "out.geojson"
    buffer_file(src, dst, distance=500, unit="meters", dissolve=False)
    assert dst.exists()
    result = gpd.read_file(str(dst))
    assert len(result) == 0
