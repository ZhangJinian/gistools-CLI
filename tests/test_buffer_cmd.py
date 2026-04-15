import pytest
from click.testing import CliRunner
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def point_geojson(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[Point(114.0, 22.5)],
        crs="EPSG:4326",
    )
    p = tmp_path / "point.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p


def test_buffer_basic(runner, point_geojson, tmp_path):
    result = runner.invoke(cli, [
        "buffer",
        str(point_geojson),
        str(tmp_path / "out.geojson"),
        "--distance", "500",
    ])
    assert result.exit_code == 0
    assert (tmp_path / "out.geojson").exists()


def test_buffer_km_unit(runner, point_geojson, tmp_path):
    result = runner.invoke(cli, [
        "buffer", str(point_geojson), str(tmp_path / "out.geojson"),
        "--distance", "1", "--unit", "km",
    ])
    assert result.exit_code == 0


def test_buffer_dissolve(runner, tmp_path):
    gdf = gpd.GeoDataFrame(
        geometry=[Point(114.0, 22.5), Point(114.001, 22.501)],
        crs="EPSG:4326",
    )
    src = tmp_path / "pts.geojson"
    gdf.to_file(str(src), driver="GeoJSON")
    result = runner.invoke(cli, [
        "buffer", str(src), str(tmp_path / "out.geojson"),
        "--distance", "500", "--dissolve",
    ])
    assert result.exit_code == 0


def test_buffer_rejects_raster(runner, tmp_path):
    """传入栅格文件应立即报错"""
    from osgeo import gdal
    import numpy as np
    fake_tif = tmp_path / "dem.tif"
    ds = gdal.GetDriverByName("GTiff").Create(str(fake_tif), 10, 10, 1, gdal.GDT_Byte)
    ds.SetGeoTransform([0, 1, 0, 0, 0, -1])
    ds.GetRasterBand(1).WriteArray(np.zeros((10, 10), dtype=np.uint8))
    ds = None
    result = runner.invoke(cli, [
        "buffer", str(fake_tif), str(tmp_path / "out.geojson"),
        "--distance", "500",
    ])
    assert result.exit_code == 1
    # error message is in exception (Click exception handling)
    assert result.exception is not None


def test_buffer_missing_distance(runner, point_geojson, tmp_path):
    result = runner.invoke(cli, [
        "buffer", str(point_geojson), str(tmp_path / "out.geojson"),
    ])
    assert result.exit_code == 2


def test_buffer_batch(runner, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    gdf = gpd.GeoDataFrame(geometry=[Point(114.0, 22.5)], crs="EPSG:4326")
    gdf.to_file(str(src_dir / "a.geojson"), driver="GeoJSON")
    result = runner.invoke(cli, [
        "buffer", str(src_dir), str(tmp_path / "dst"), "--distance", "500",
    ])
    assert result.exit_code in (0, 1)
    assert "成功" in result.output
