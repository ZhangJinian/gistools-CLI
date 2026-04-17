"""
GDAL Polygonize / Rasterize / 栅格像元遍历核心实现。
"""
from pathlib import Path
import numpy as np
from osgeo import gdal, ogr, osr
import geopandas as gpd


def raster_to_polygon(src_path, dst_path, band_field="DN", simplify_tol=None, multi=False):
    """
    栅格 → 面矢量。

    Parameters
    ----------
    src_path : Path
        输入栅格路径。
    dst_path : Path
        输出矢量路径（.shp / .geojson 等）。
    band_field : str
        栅格值写入属性表的字段名，默认 "DN"。
    simplify_tol : float, optional
        几何简化容差（GDAL 单位），None 表示不简化。
    multi : bool
        是否合并为单一 MultiPolygon 输出。
    """
    src_ds = gdal.Open(str(src_path))
    if src_ds is None:
        raise RuntimeError("无法读取栅格文件：{}".format(src_path))

    band = src_ds.GetRasterBand(1)
    mask = band.GetMaskBand()

    # 建立输出矢量
    ext = dst_path.suffix.lower()
    if ext == ".shp":
        drv = ogr.GetDriverByName("ESRI Shapefile")
    elif ext == ".geojson":
        drv = ogr.GetDriverByName("GeoJSON")
    elif ext == ".kml":
        drv = ogr.GetDriverByName("KML")
    elif ext == ".gml":
        drv = ogr.GetDriverByName("GML")
    elif ext == ".gpkg":
        drv = ogr.GetDriverByName("GPKG")
    else:
        drv = ogr.GetDriverByName("ESRI Shapefile")

    if dst_path.exists():
        drv.DeleteDataSource(str(dst_path))
    dst_ds = drv.CreateDataSource(str(dst_path))

    # 从输入栅格复制投影信息
    srs = osr.SpatialReference()
    srs.ImportFromWkt(src_ds.GetProjection())
    geom_type = ogr.wkbMultiPolygon if multi else ogr.wkbPolygon

    dst_layer = dst_ds.CreateLayer(dst_path.stem, srs=srs, geom_type=geom_type)

    # 添加字段
    field_defn = ogr.FieldDefn(band_field, ogr.OFTInteger)
    dst_layer.CreateField(field_defn)
    field_index = dst_layer.FindFieldIndex(band_field, 1)

    # 调用 Polygonize
    gdal.Polygonize(band, mask, dst_layer, field_index, options=[])

    # 几何简化
    if simplify_tol and simplify_tol > 0:
        feat = dst_layer.GetNextFeature()
        while feat:
            geom = feat.GetGeometryRef()
            geom.Simplify(simplify_tol)
            dst_layer.SetFeature(feat)
            feat = dst_layer.GetNextFeature()

    # 合并为 MultiPolygon
    if multi:
        all_geoms = []
        feat = dst_layer.GetNextFeature()
        while feat:
            geom = feat.GetGeometryRef()
            if geom:
                for i in range(geom.GetGeometryCount()):
                    sub = geom.GetGeometryRef(i)
                    all_geoms.append(sub.Clone())
            feat = dst_layer.GetNextFeature()

        dst_ds.DeleteLayer(dst_layer)
        out_layer = dst_ds.CreateLayer(dst_path.stem, srs=srs, geom_type=ogr.wkbMultiPolygon)
        out_layer.CreateField(ogr.FieldDefn(band_field, ogr.OFTInteger))
        if all_geoms:
            multi_geom = ogr.ForceToMultiPolygon(ogr.BuildGeometryFromCount(all_geoms, False) if hasattr(ogr, 'BuildGeometryFromCount') else None)
            if multi_geom is None:
                multi_geom = ogr.Geometry(ogr.wkbMultiPolygon)
                for g in all_geoms:
                    multi_geom.AddGeometry(g)
            feat_out = ogr.Feature(out_layer.GetLayerDefn())
            feat_out.SetGeometry(multi_geom)
            out_layer.CreateFeature(feat_out)

    dst_ds.FlushCache()
    dst_ds = None
    src_ds = None


def raster_to_point(src_path, dst_path, band_field="value"):
    """
    栅格 → 点矢量（每个有效像元中心一个点）。

    Parameters
    ----------
    src_path : Path
        输入栅格路径。
    dst_path : Path
        输出矢量路径（.shp / .geojson）。
    band_field : str
        像元值写入的字段名，默认 "value"。
    """
    src_ds = gdal.Open(str(src_path))
    if src_ds is None:
        raise RuntimeError("无法读取栅格文件：{}".format(src_path))

    band = src_ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    gt = src_ds.GetGeoTransform()

    # 建立输出矢量
    ext = dst_path.suffix.lower()
    if ext == ".shp":
        drv = ogr.GetDriverByName("ESRI Shapefile")
    elif ext == ".geojson":
        drv = ogr.GetDriverByName("GeoJSON")
    elif ext == ".kml":
        drv = ogr.GetDriverByName("KML")
    elif ext == ".gml":
        drv = ogr.GetDriverByName("GML")
    elif ext == ".gpkg":
        drv = ogr.GetDriverByName("GPKG")
    else:
        drv = ogr.GetDriverByName("ESRI Shapefile")

    if dst_path.exists():
        drv.DeleteDataSource(str(dst_path))
    dst_ds = drv.CreateDataSource(str(dst_path))

    srs = osr.SpatialReference()
    srs.ImportFromWkt(src_ds.GetProjection())
    dst_layer = dst_ds.CreateLayer(dst_path.stem, srs=srs, geom_type=ogr.wkbPoint)

    field_defn = ogr.FieldDefn(band_field, ogr.OFTReal)
    dst_layer.CreateField(field_defn)

    # 遍历像元
    cols = src_ds.RasterXSize
    rows = src_ds.RasterYSize
    data = band.ReadAsArray(0, 0, cols, rows)

    for row in range(rows):
        for col in range(cols):
            val = data[row, col]
            if nodata is not None and val == nodata:
                continue
            # 像元中心坐标
            x = gt[0] + (col + 0.5) * gt[1] + (row + 0.5) * gt[2]
            y = gt[3] + (col + 0.5) * gt[4] + (row + 0.5) * gt[5]

            pt = ogr.Geometry(ogr.wkbPoint)
            pt.SetPoint_2D(0, x, y)

            feat = ogr.Feature(dst_layer.GetLayerDefn())
            feat.SetGeometry(pt)
            feat.SetField(band_field, float(val))
            dst_layer.CreateFeature(feat)
            feat = None

    dst_ds.FlushCache()
    dst_ds = None
    src_ds = None


def feature_to_raster(src_path, dst_path, cellsize, field=None, extent=None):
    """
    矢量 → 栅格。

    Parameters
    ----------
    src_path : Path
        输入矢量路径（SHP/GeoJSON 等）。
    dst_path : Path
        输出栅格路径（.tif 等）。
    cellsize : float
        像元大小（GDAL 单位）。
    field : str, optional
        用于填入栅格的字段名；None 时填 1。
    extent : tuple, optional
        (xmin, ymin, xmax, ymax)，None 时自动从矢量外包范围计算。
    """
    src_ds = ogr.Open(str(src_path))
    if src_ds is None:
        raise RuntimeError("无法读取矢量文件：{}".format(src_path))

    src_layer = src_ds.GetLayer()

    if extent is None:
        # 从矢量外包范围计算
        extent_obj = src_layer.GetExtent()  # (xmin, xmax, ymin, ymax)
        xmin, xmax, ymin, ymax = extent_obj
        # 扩大半个像元
        xmin -= cellsize / 2
        xmax += cellsize / 2
        ymin -= cellsize / 2
        ymax += cellsize / 2
    else:
        xmin, ymin, xmax, ymax = extent

    x_res = max(1, int(round((xmax - xmin) / cellsize)))
    y_res = max(1, int(round((ymax - ymin) / cellsize)))

    drv = gdal.GetDriverByName("GTiff")
    if drv is None:
        raise RuntimeError("GDAL 不支持 GTiff 驱动")

    if dst_path.exists():
        dst_path.unlink()

    dst_ds = drv.Create(str(dst_path), x_res, y_res, 1, gdal.GDT_Int32)
    if dst_ds is None:
        raise RuntimeError("无法创建栅格文件：{}".format(dst_path))

    # 设置仿射变换
    gt = [xmin, cellsize, 0, ymax, 0, -cellsize]
    dst_ds.SetGeoTransform(gt)

    # 设置投影
    src_srs = src_layer.GetSpatialRef()
    if src_srs:
        dst_ds.SetProjection(src_srs.ExportToWkt())

    # Rasterize
    if field:
        gdal.RasterizeLayer(dst_ds, [1], src_layer, options=[f"ATTRIBUTE={field}"])
    else:
        gdal.RasterizeLayer(dst_ds, [1], src_layer, burn_values=[1])

    dst_ds.FlushCache()
    dst_ds = None
    src_ds = None
