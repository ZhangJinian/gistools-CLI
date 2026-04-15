from pathlib import Path
from typing import Tuple, Optional

from osgeo import ogr, gdal

VECTOR_DRIVERS = {
    ".shp": "ESRI Shapefile",
    ".geojson": "GeoJSON",
    ".kml": "KML",
    ".gml": "GML",
    ".gpkg": "GPKG",
    ".csv": "CSV",
}

RASTER_DRIVERS = {
    ".tif": "GTiff",
    ".tiff": "GTiff",
    ".img": "HFA",
    ".hdf": "HDF4",
    ".nc": "netCDF",
}


def detect_format(path):
    """返回 ('vector'|'raster', driver_name)，格式不支持则抛 ValueError。"""
    ext = path.suffix.lower()
    if ext in VECTOR_DRIVERS:
        return "vector", VECTOR_DRIVERS[ext]
    if ext in RASTER_DRIVERS:
        return "raster", RASTER_DRIVERS[ext]
    raise ValueError("不支持的格式：{}".format(ext))


def convert_vector(src, dst, driver):
    """矢量格式转换，dst 已存在时自动覆盖。"""
    src_ds = ogr.Open(str(src))
    if src_ds is None:
        raise RuntimeError("无法读取文件：{}\n请确认文件完整（SHP 需要 .dbf / .prj 同目录）".format(src))
    drv = ogr.GetDriverByName(driver)
    if drv is None:
        raise RuntimeError("GDAL 不支持驱动：{}".format(driver))
    if dst.exists():
        drv.DeleteDataSource(str(dst))
    out_ds = drv.CopyDataSource(src_ds, str(dst))
    if out_ds is None:
        raise RuntimeError("写出失败：{}".format(dst))
    out_ds.FlushCache()
    out_ds = None
    src_ds = None


def convert_raster(src, dst, driver):
    """栅格格式转换，dst 已存在时自动覆盖。"""
    src_ds = gdal.Open(str(src))
    if src_ds is None:
        raise RuntimeError("无法读取栅格文件：{}".format(src))
    if dst.exists():
        dst.unlink()
    drv = gdal.GetDriverByName(driver)
    if drv is None:
        raise RuntimeError("GDAL 不支持驱动：{}".format(driver))
    out_ds = drv.CreateCopy(str(dst), src_ds)
    if out_ds is None:
        raise RuntimeError("栅格写出失败：{}".format(dst))
    out_ds.FlushCache()
    out_ds = None
    src_ds = None
