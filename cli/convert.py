"""
convert 命令组 — GIS 格式转换工具箱。
"""
import sys
from pathlib import Path
import click
from core.rasterize import raster_to_polygon, raster_to_point, feature_to_raster
from core.formats import convert_vector, convert_raster, detect_format, VECTOR_DRIVERS, RASTER_DRIVERS
from core.batch import collect_input_files, report_errors


@click.group()
def convert():
    """GIS 格式转换工具箱（convert 子命令入口）"""
    pass


# ---------------------------------------------------------------------------
# raster2polygon — 栅格 → 面要素
# ---------------------------------------------------------------------------
@convert.command("raster2polygon")
@click.argument("input_raster", metavar="<input_raster>", type=click.Path(exists=True))
@click.argument("output_polygon", metavar="<output_polygon>", type=click.Path(exists=False))
@click.option("--field", default="DN", help="栅格值写入属性表的字段名，默认 DN")
@click.option("--simplify", type=float, default=None, help="几何简化容差（GDAL 单位），默认不简化")
@click.option("--multi", is_flag=True, help="输出多部件（MultiPolygon），默认否")
def raster2polygon(input_raster, output_polygon, field, simplify, multi):
    """栅格转面要素（参考 ArcGIS Raster To Polygon）。"""
    src = Path(input_raster)
    dst = Path(output_polygon)

    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "raster":
        click.echo("✗ 输入不是栅格文件：{}".format(src))
        sys.exit(1)

    try:
        raster_to_polygon(src, dst, band_field=field, simplify_tol=simplify, multi=multi)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# raster2point — 栅格 → 点要素
# ---------------------------------------------------------------------------
@convert.command("raster2point")
@click.argument("input_raster", metavar="<input_raster>", type=click.Path(exists=True))
@click.argument("output_point", metavar="<output_point>", type=click.Path(exists=False))
@click.option("--field", default="value", help="像元值写入字段名，默认 value")
def raster2point(input_raster, output_point, field):
    """栅格转点要素（参考 ArcGIS Raster To Point）。"""
    src = Path(input_raster)
    dst = Path(output_point)

    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "raster":
        click.echo("✗ 输入不是栅格文件：{}".format(src))
        sys.exit(1)

    try:
        raster_to_point(src, dst, band_field=field)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# shp2raster — 矢量 → 栅格
# ---------------------------------------------------------------------------
@convert.command("shp2raster")
@click.argument("input_shp", metavar="<input_shp>", type=click.Path(exists=True))
@click.argument("output_raster", metavar="<output_raster>", type=click.Path(exists=False))
@click.option("--cellsize", type=float, required=True, help="像元大小（必填，GDAL 单位）")
@click.option("--field", default=None, help="用于填入栅格的字段，默认填 1")
@click.option("--extent", default=None, help="输出范围 xmin ymin xmax ymax，默认从矢量外包自动计算")
def shp2raster(input_shp, output_raster, cellsize, field, extent):
    """矢量转栅格（参考 ArcGIS Feature To Raster）。"""
    src = Path(input_shp)
    dst = Path(output_raster)

    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "vector":
        click.echo("✗ 输入不是矢量文件：{}".format(src))
        sys.exit(1)

    if extent:
        try:
            coords = [float(x) for x in extent.split()]
            if len(coords) != 4:
                raise ValueError()
        except (ValueError, TypeError):
            click.echo("✗ --extent 必须为 4 个数值：xmin ymin xmax ymax")
            sys.exit(2)
        extent_tuple = tuple(coords)
    else:
        extent_tuple = None

    try:
        feature_to_raster(src, dst, cellsize=cellsize, field=field, extent=extent_tuple)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# shp2geojson — SHP → GeoJSON
# ---------------------------------------------------------------------------
@convert.command("shp2geojson")
@click.argument("input_shp", metavar="<input_shp>", type=click.Path(exists=True))
@click.argument("output_geojson", metavar="<output_geojson>", type=click.Path(exists=False))
@click.option("--encoding", default="UTF-8", help="输出编码，默认 UTF-8")
def shp2geojson(input_shp, output_geojson, encoding):
    """SHP 转 GeoJSON（参考 ArcGIS To GeoJSON）。"""
    src = Path(input_shp)
    dst = Path(output_geojson)

    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "vector":
        click.echo("✗ 输入不是矢量文件：{}".format(src))
        sys.exit(1)

    # 设置环境编码（OGR 环境变量）
    import os
    old_enc = os.environ.get("SHAPE_ENCODING", "")
    os.environ["SHAPE_ENCODING"] = encoding

    try:
        convert_vector(src, dst, "GeoJSON")
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)
    finally:
        os.environ["SHAPE_ENCODING"] = old_enc


# ---------------------------------------------------------------------------
# geojson2shp — GeoJSON → SHP
# ---------------------------------------------------------------------------
@convert.command("geojson2shp")
@click.argument("input_geojson", metavar="<input_geojson>", type=click.Path(exists=True))
@click.argument("output_shp", metavar="<output_shp>", type=click.Path(exists=False))
@click.option("--encoding", default="UTF-8", help="输入文件编码，默认 UTF-8")
def geojson2shp(input_geojson, output_shp, encoding):
    """GeoJSON 转 SHP（参考 ArcGIS To SHP）。"""
    src = Path(input_geojson)
    dst = Path(output_shp)

    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "vector":
        click.echo("✗ 输入不是矢量文件：{}".format(src))
        sys.exit(1)

    import os
    old_enc = os.environ.get("SHAPE_ENCODING", "")
    os.environ["SHAPE_ENCODING"] = encoding

    try:
        convert_vector(src, dst, "ESRI Shapefile")
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)
    finally:
        os.environ["SHAPE_ENCODING"] = old_enc
