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
def shp_no_crs(tmp_path):
    """无 CRS 的 SHP（geopandas 写 crs=None 时不写 .prj）"""
    gdf = gpd.GeoDataFrame(geometry=[Point(114.0, 22.5)], crs=None)
    # SHP 会写到目录
    shp_dir = tmp_path / "nocrs"
    gdf.to_file(str(shp_dir))
    return shp_dir


@pytest.fixture
def geojson_wgs84(tmp_path):
    """WGS84 GeoJSON"""
    gdf = gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    )
    p = tmp_path / "wgs84.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p


def test_reproject_epsg_to_epsg(runner, geojson_wgs84, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(geojson_wgs84),
        str(tmp_path / "out.geojson"),
        "--to", "EPSG:4490",
    ])
    assert result.exit_code == 0
    out = gpd.read_file(tmp_path / "out.geojson")
    assert out.crs.to_epsg() == 4490


def test_reproject_alias_cgcs2000(runner, geojson_wgs84, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(geojson_wgs84),
        str(tmp_path / "out.geojson"),
        "--to", "CGCS2000",
    ])
    assert result.exit_code == 0
    out = gpd.read_file(tmp_path / "out.geojson")
    assert out.crs.to_epsg() == 4490


def test_reproject_chinese_alias(runner, geojson_wgs84, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(geojson_wgs84),
        str(tmp_path / "out.geojson"),
        "--to", "国家2000",
    ])
    assert result.exit_code == 0


def test_reproject_no_crs_without_from(runner, shp_no_crs, tmp_path):
    """SHP 目录无 CRS 且未传 --from → 报错提示使用 --from"""
    result = runner.invoke(cli, [
        "reproject",
        str(shp_no_crs),
        str(tmp_path / "out"),
        "--to", "CGCS2000",
    ])
    assert result.exit_code == 1
    assert "--from" in result.output


def test_reproject_explicit_from(runner, geojson_wgs84, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(geojson_wgs84),
        str(tmp_path / "out.geojson"),
        "--to", "CGCS2000",
        "--from", "WGS84",
    ])
    assert result.exit_code == 0


def test_reproject_unknown_crs(runner, geojson_wgs84, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(geojson_wgs84),
        str(tmp_path / "out.geojson"),
        "--to", "火星坐标系XYZ",
    ])
    assert result.exit_code == 1
    assert "无法识别" in result.output


def test_reproject_batch(runner, tmp_path):
    """批量转投影"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    gdf = gpd.GeoDataFrame(geometry=[Point(114.0, 22.5)], crs="EPSG:4326")
    gdf.to_file(str(src_dir / "a.geojson"), driver="GeoJSON")
    gdf.to_file(str(src_dir / "b.geojson"), driver="GeoJSON")
    dst_dir = tmp_path / "dst"
    result = runner.invoke(cli, [
        "reproject",
        str(src_dir),
        str(dst_dir),
        "--to", "CGCS2000",
        "--from", "WGS84",
    ])
    assert result.exit_code == 0
    assert "成功" in result.output
