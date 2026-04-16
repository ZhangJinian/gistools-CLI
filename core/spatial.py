import geopandas as gpd
import click


def buffer_file(src, dst, distance, unit, dissolve):
    """
    对矢量文件做缓冲区分析。
    unit: 'meters' | 'km' | 'degrees'
    dissolve: 是否合并所有缓冲要素为单一几何
    """
    gdf = gpd.read_file(str(src))

    if len(gdf) == 0:
        click.echo("⚠ 输入数据无要素，输出为空文件：{}".format(dst.name))
        empty = gdf.copy()
        empty.to_file(str(dst), driver="GeoJSON")
        return

    if unit == "km":
        distance_m = distance * 1000
    elif unit == "meters":
        distance_m = distance
    else:
        # degrees
        distance_m = None

    if unit in ("meters", "km"):
        # 转换到合适的投影坐标系以米为单位做 buffer
        crs_orig = gdf.crs
        if crs_orig is None:
            raise RuntimeError(
                "文件无坐标系信息，无法使用米为单位做缓冲区。"
                "请先用 gistools reproject 赋予坐标系，或使用 --unit degrees"
            )
        gdf_proj = gdf.to_crs(gdf.estimate_utm_crs())
        buffered = gdf_proj.copy()
        buffered.geometry = gdf_proj.geometry.buffer(distance_m)
        buffered = buffered.to_crs(crs_orig)
    else:
        # degrees 单位，直接 buffer
        buffered = gdf.copy()
        buffered.geometry = gdf.geometry.buffer(distance)

    if dissolve:
        buffered = buffered.dissolve()

    dst.parent.mkdir(parents=True, exist_ok=True)
    ext = dst.suffix.lower()
    driver = {
        ".shp": "ESRI Shapefile",
        ".geojson": "GeoJSON",
        ".kml": "KML",
        ".gml": "GML",
        ".gpkg": "GPKG",
        ".csv": "CSV",
    }.get(ext, "GeoJSON")
    buffered.to_file(str(dst), driver=driver)
