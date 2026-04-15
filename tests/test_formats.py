import pytest
from pathlib import Path
from core.formats import detect_format, convert_vector, VECTOR_DRIVERS


def test_detect_geojson():
    kind, driver = detect_format(Path("foo.geojson"))
    assert kind == "vector"
    assert driver == "GeoJSON"


def test_detect_shp():
    kind, driver = detect_format(Path("foo.shp"))
    assert kind == "vector"
    assert driver == "ESRI Shapefile"


def test_detect_tiff():
    kind, driver = detect_format(Path("foo.tif"))
    assert kind == "raster"
    assert driver == "GTiff"


def test_detect_unsupported():
    with pytest.raises(ValueError, match="不支持的格式"):
        detect_format(Path("foo.xyz"))


def test_convert_vector_shp_to_geojson(sample_dir, tmp_path):
    src = sample_dir / "points.shp"
    dst = tmp_path / "out.geojson"
    convert_vector(src, dst, "GeoJSON")
    assert dst.exists()
    import geopandas as gpd
    gdf = gpd.read_file(dst)
    assert len(gdf) == 2


def test_convert_vector_geojson_to_shp(sample_dir, tmp_path):
    src = sample_dir / "points.geojson"
    dst = tmp_path / "out.shp"
    convert_vector(src, dst, "ESRI Shapefile")
    assert dst.exists()


def test_convert_vector_overwrite(sample_dir, tmp_path):
    """同名文件自动覆盖，不报错"""
    src = sample_dir / "points.geojson"
    dst = tmp_path / "out.geojson"
    convert_vector(src, dst, "GeoJSON")
    convert_vector(src, dst, "GeoJSON")  # 第二次不应报错
    assert dst.exists()
