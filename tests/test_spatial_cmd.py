import pytest
from pathlib import Path
from osgeo import gdal, ogr
import numpy as np

DEM_PATH = Path(__file__).parent.parent / "testdata" / "LRMS.tif"

def test_dem_exists():
    assert DEM_PATH.exists(), f"DEM not found: {DEM_PATH}"

def test_slope_degree(tmp_path):
    from core.dem import calculate_slope
    dst = tmp_path / "slope_degree.tif"
    calculate_slope(DEM_PATH, dst, unit="DEGREE", scale=1.0)
    assert dst.exists()
    ds = gdal.Open(str(dst))
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    valid = data[data >= 0]
    assert valid.max() <= 90.0
    ds = None

def test_slope_percent(tmp_path):
    from core.dem import calculate_slope
    dst = tmp_path / "slope_percent.tif"
    calculate_slope(DEM_PATH, dst, unit="PERCENT", scale=1.0)
    assert dst.exists()
    ds = gdal.Open(str(dst))
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    valid = data[data >= 0]
    assert valid.max() > 0
    ds = None

def test_slope_cli(tmp_path):
    from click.testing import CliRunner
    from cli.main import cli
    dst = tmp_path / "slope.tif"
    runner = CliRunner()
    result = runner.invoke(cli, ["spatial", "slope", str(DEM_PATH), str(dst)])
    assert result.exit_code == 0, result.output
    assert dst.exists()

def test_aspect(tmp_path):
    from core.dem import calculate_aspect
    dst = tmp_path / "aspect.tif"
    calculate_aspect(DEM_PATH, dst)
    assert dst.exists()
    ds = gdal.Open(str(dst))
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    valid = data[data >= 0]
    assert valid.max() <= 360.0
    ds = None

def test_aspect_cli(tmp_path):
    from click.testing import CliRunner
    from cli.main import cli
    dst = tmp_path / "aspect.tif"
    runner = CliRunner()
    result = runner.invoke(cli, ["spatial", "aspect", str(DEM_PATH), str(dst)])
    assert result.exit_code == 0, result.output
    assert dst.exists()

def test_hillshade(tmp_path):
    from core.dem import calculate_hillshade
    dst = tmp_path / "hillshade.tif"
    calculate_hillshade(DEM_PATH, dst, azimuth=315, altitude=45, scale=1.0)
    assert dst.exists()
    ds = gdal.Open(str(dst))
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    assert data.max() <= 255 and data.min() >= 0
    ds = None

def test_hillshade_custom_params(tmp_path):
    from core.dem import calculate_hillshade
    dst = tmp_path / "hillshade_custom.tif"
    calculate_hillshade(DEM_PATH, dst, azimuth=180, altitude=30, scale=2.0)
    assert dst.exists()
    ds = gdal.Open(str(dst))
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    assert data.max() <= 255
    ds = None

def test_hillshade_cli(tmp_path):
    from click.testing import CliRunner
    from cli.main import cli
    dst = tmp_path / "hillshade.tif"
    runner = CliRunner()
    result = runner.invoke(cli, ["spatial", "hillshade", str(DEM_PATH), str(dst)])
    assert result.exit_code == 0, result.output
    assert dst.exists()

def test_hillshade_cli_with_options(tmp_path):
    from click.testing import CliRunner
    from cli.main import cli
    dst = tmp_path / "hillshade.tif"
    runner = CliRunner()
    result = runner.invoke(cli, ["spatial", "hillshade", str(DEM_PATH), str(dst), "--azimuth", "180", "--altitude", "30", "--scale", "2.0"])
    assert result.exit_code == 0, result.output
    assert dst.exists()

def test_contour(tmp_path):
    from core.dem import generate_contour
    dst = tmp_path / "contour.geojson"
    generate_contour(DEM_PATH, dst, interval=10, start=0, field="ELEV")
    assert dst.exists()
    ds = ogr.Open(str(dst))
    layer = ds.GetLayer(0)
    assert layer.GetFeatureCount() > 0
    ds = None

def test_contour_custom_params(tmp_path):
    from core.dem import generate_contour
    dst = tmp_path / "contour_custom.geojson"
    generate_contour(DEM_PATH, dst, interval=5, start=5, field="ELEV2")
    assert dst.exists()
    ds = ogr.Open(str(dst))
    layer = ds.GetLayer(0)
    assert layer.GetFeatureCount() > 0
    ds = None

def test_contour_cli(tmp_path):
    from click.testing import CliRunner
    from cli.main import cli
    dst = tmp_path / "contour.geojson"
    runner = CliRunner()
    result = runner.invoke(cli, ["spatial", "contour", str(DEM_PATH), str(dst), "--interval", "10"])
    assert result.exit_code == 0, result.output
    assert dst.exists()

def test_contour_cli_with_options(tmp_path):
    from click.testing import CliRunner
    from cli.main import cli
    dst = tmp_path / "contour.geojson"
    runner = CliRunner()
    result = runner.invoke(cli, ["spatial", "contour", str(DEM_PATH), str(dst), "--interval", "5", "--start", "5", "--field", "ELEV2"])
    assert result.exit_code == 0, result.output
    assert dst.exists()

def test_contour_cli_missing_interval():
    from click.testing import CliRunner
    from cli.main import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["spatial", "contour", str(DEM_PATH), "/tmp/c.geojson"])
    assert result.exit_code != 0
