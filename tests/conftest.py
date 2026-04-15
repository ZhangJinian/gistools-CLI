import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString
from pathlib import Path


@pytest.fixture(scope="session")
def sample_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("sample")

    # WGS84 点要素 GeoJSON
    gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    ).to_file(d / "points.geojson", driver="GeoJSON")

    # WGS84 点要素 SHP
    gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    ).to_file(d / "points.shp")

    # 线要素 GeoJSON
    gpd.GeoDataFrame(
        {"name": ["road"]},
        geometry=[LineString([(114.0, 22.5), (114.1, 22.6)])],
        crs="EPSG:4326",
    ).to_file(d / "line.geojson", driver="GeoJSON")

    return d
