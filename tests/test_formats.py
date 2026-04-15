import geopandas as gpd
import pytest
from pathlib import Path
from core.formats import detect_format, convert_vector, convert_raster


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


def test_convert_raster_gtiff_to_img(tmp_path):
    """使用 GDAL 创建真实 GTiff，转换为 HFA/IMG 格式，验证输出存在"""
    from osgeo import gdal
    import numpy as np

    src_tif = tmp_path / "test.tif"
    ds = gdal.GetDriverByName("GTiff").Create(str(src_tif), 100, 100, 1, gdal.GDT_Byte)
    ds.SetProjection('GEOGCS["WGS84", Datum["WGS84"]]')
    ds.SetGeoTransform([0, 1, 0, 0, 0, -1])
    ds.GetRasterBand(1).WriteArray(np.zeros((100, 100), dtype=np.uint8))
    ds = None

    dst_img = tmp_path / "test.img"
    convert_raster(src_tif, dst_img, "HFA")
    assert dst_img.exists()


from core.batch import collect_input_files, report_errors

def test_collect_input_files(sample_dir):
    files = collect_input_files(sample_dir, {".geojson", ".shp"})
    exts = {f.suffix for f in files}
    assert ".geojson" in exts
    assert ".shp" in exts

def test_collect_input_files_empty(tmp_path):
    files = collect_input_files(tmp_path, {".geojson"})
    assert files == []

def test_report_errors_few(capsys):
    errors = [("a.shp", "缺少.prj"), ("b.shp", "文件损坏")]
    wrote_log = report_errors(errors, log_path=None)
    captured = capsys.readouterr()
    assert "a.shp" in captured.out
    assert wrote_log is False

def test_report_errors_many(tmp_path, capsys):
    errors = [(f"file_{i:02d}.shp", "错误") for i in range(15)]
    log = tmp_path / "gistools-errors.log"
    wrote_log = report_errors(errors, log_path=log)
    captured = capsys.readouterr()
    assert "还有" in captured.out
    assert log.exists()
    assert wrote_log is True
