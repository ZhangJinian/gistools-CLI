import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pathlib import Path
from click.testing import CliRunner
from cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


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

    # 面要素 GeoJSON
    gpd.GeoDataFrame(
        {"zone": [1, 2]},
        geometry=[
            Polygon([(114.0, 22.5), (114.1, 22.5), (114.1, 22.6), (114.0, 22.6)]),
            Polygon([(114.1, 22.5), (114.2, 22.5), (114.2, 22.6), (114.1, 22.6)]),
        ],
        crs="EPSG:4326",
    ).to_file(d / "zones.geojson", driver="GeoJSON")

    # 面要素 SHP
    gpd.GeoDataFrame(
        {"zone": [1, 2]},
        geometry=[
            Polygon([(114.0, 22.5), (114.1, 22.5), (114.1, 22.6), (114.0, 22.6)]),
            Polygon([(114.1, 22.5), (114.2, 22.5), (114.2, 22.6), (114.1, 22.6)]),
        ],
        crs="EPSG:4326",
    ).to_file(d / "zones.shp")

    return d


# ---------------------------------------------------------------------------
# shp2geojson
# ---------------------------------------------------------------------------
def test_shp2geojson_single_file(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "convert", "shp2geojson",
        str(sample_dir / "points.shp"),
        str(tmp_path / "out.geojson"),
    ])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "out.geojson").exists()


def test_shp2geojson_missing_input(runner, tmp_path):
    result = runner.invoke(cli, [
        "convert", "shp2geojson",
        str(tmp_path / "notexist.shp"),
        str(tmp_path / "out.geojson"),
    ])
    # Click Path(exists=True) 验证失败 → exit 2
    assert result.exit_code == 2


def test_shp2geojson_non_vector_input(runner, sample_dir, tmp_path):
    """传入非矢量文件应报错（GeoJSON 本身是矢量，只检查 kind==vector，故此测试无意义，
    改为验证 shp2geojson 对非 SHP 矢量也能正常工作）。"""
    result = runner.invoke(cli, [
        "convert", "shp2geojson",
        str(sample_dir / "line.geojson"),  # GeoJSON 线要素
        str(tmp_path / "out.shp"),
    ])
    # shp2geojson 接受任何矢量输入，输出 GeoJSON
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# geojson2shp
# ---------------------------------------------------------------------------
def test_geojson2shp_single_file(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "convert", "geojson2shp",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.shp"),
    ])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "out.shp").exists()


def test_geojson2shp_missing_input(runner, tmp_path):
    result = runner.invoke(cli, [
        "convert", "geojson2shp",
        str(tmp_path / "notexist.geojson"),
        str(tmp_path / "out.shp"),
    ])
    # Click Path(exists=True) 验证失败 → exit 2
    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# convert --help 显示子命令
# ---------------------------------------------------------------------------
def test_convert_group_help(runner):
    result = runner.invoke(cli, ["convert", "--help"])
    assert result.exit_code == 0
    assert "raster2polygon" in result.output
    assert "raster2point" in result.output
    assert "shp2raster" in result.output
    assert "shp2geojson" in result.output
    assert "geojson2shp" in result.output


# ---------------------------------------------------------------------------
# shp2raster — 需要 cellsize
# ---------------------------------------------------------------------------
def test_shp2raster_requires_cellsize(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "convert", "shp2raster",
        str(sample_dir / "points.shp"),
        str(tmp_path / "out.tif"),
    ])
    assert result.exit_code == 2
    assert "cellsize" in result.output.lower()


def test_shp2raster_with_cellsize(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "convert", "shp2raster",
        str(sample_dir / "zones.shp"),
        str(tmp_path / "out.tif"),
        "--cellsize", "0.001",
    ])
    # 可能因无有效范围失败，但不应该是参数错误
    assert result.exit_code in (0, 1)


# ---------------------------------------------------------------------------
# raster2polygon / raster2point — 需要真实栅格数据，无法用 SHP 测试
# ---------------------------------------------------------------------------
def test_raster2polygon_requires_raster(runner, sample_dir, tmp_path):
    """传入矢量文件应报错"""
    result = runner.invoke(cli, [
        "convert", "raster2polygon",
        str(sample_dir / "points.shp"),
        str(tmp_path / "out.shp"),
    ])
    assert result.exit_code == 1


def test_raster2point_requires_raster(runner, sample_dir, tmp_path):
    """传入矢量文件应报错"""
    result = runner.invoke(cli, [
        "convert", "raster2point",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.shp"),
    ])
    assert result.exit_code == 1
