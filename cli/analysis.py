"""
Analysis 工具箱 CLI — 裁剪 / 交集 / 合并 / 融合 / 空间连接
"""
import sys
from pathlib import Path
import click
import geopandas as gpd

from core import analysis as _core


def _read(path):
    try:
        return gpd.read_file(path)
    except Exception as exc:
        click.echo("Cannot read {}: {}".format(path, exc))
        sys.exit(1)


def _write(gdf, path):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    driver = "GeoJSON" if out.suffix.lower() == ".geojson" else None
    try:
        if driver:
            gdf.to_file(path, driver=driver)
        else:
            gdf.to_file(path)
        click.echo("✓ 结果已保存：{}".format(path))
    except Exception as exc:
        click.echo("✗ 写出失败：{}".format(exc))
        sys.exit(1)


@click.group()
def analysis():
    """Analysis 工具箱 — 空间分析操作（裁剪 / 交集 / 合并 / 融合 / 空间连接）"""
    pass


@analysis.command("clip")
@click.argument("input_features",  metavar="<input_features>")
@click.argument("clip_features",   metavar="<clip_features>")
@click.argument("output",          metavar="<output>")
def cmd_clip(input_features, clip_features, output):
    """裁剪：将 <input_features> 按 <clip_features> 的范围裁切。"""
    gdf   = _read(input_features)
    mask  = _read(clip_features)
    result = _core.clip(gdf, mask)
    _write(result, output)


@analysis.command("intersect")
@click.argument("input_features",     metavar="<input_features>")
@click.argument("intersect_features", metavar="<intersect_features>")
@click.argument("output",             metavar="<output>")
@click.option("--predicate", default="intersects",
              type=click.Choice(["intersects", "within", "contains"]),
              show_default=True, help="空间谓词")
def cmd_intersect(input_features, intersect_features, output, predicate):
    """交集：返回两个要素图层的几何重叠区域及属性。"""
    gdf   = _read(input_features)
    other = _read(intersect_features)
    if predicate != "intersects":
        joined = gpd.sjoin(gdf, other[["geometry"]], how="inner", predicate=predicate)
        gdf = gdf.loc[joined.index.unique()]
    result = _core.intersect(gdf, other)
    _write(result, output)


@analysis.command("union")
@click.argument("input_features", metavar="<input_features>")
@click.argument("union_features", metavar="<union_features>")
@click.argument("output",         metavar="<output>")
def cmd_union(input_features, union_features, output):
    """合并：将两个图层的所有要素合并输出，保留全部几何和属性。"""
    gdf_a = _read(input_features)
    gdf_b = _read(union_features)
    result = _core.union(gdf_a, gdf_b)
    _write(result, output)


@analysis.command("dissolve")
@click.argument("input_features", metavar="<input_features>")
@click.argument("output",         metavar="<output>")
@click.option("--by",        required=True, metavar="<field>", help="融合字段名（必填）")
@click.option("--multipart", is_flag=True,  help="保留多部件几何（默认拆分为单部件）")
def cmd_dissolve(input_features, output, by, multipart):
    """融合：按字段合并相邻多边形。"""
    gdf = _read(input_features)
    try:
        result = _core.dissolve(gdf, by_field=by, as_multipart=multipart)
    except ValueError as exc:
        click.echo("✗ {}".format(exc))
        sys.exit(1)
    _write(result, output)


@analysis.command("spatial-join")
@click.argument("target_features", metavar="<target_features>")
@click.argument("join_features",   metavar="<join_features>")
@click.argument("output",          metavar="<output>")
@click.option("--predicate", default="intersects",
              type=click.Choice(["intersects", "within", "contains"]),
              show_default=True, help="空间谓词")
@click.option("--how", default="left",
              type=click.Choice(["left", "right", "inner"]),
              show_default=True, help="连接类型")
def cmd_spatial_join(target_features, join_features, output, predicate, how):
    """空间连接：基于空间关系将 <join_features> 的属性关联到 <target_features>。"""
    left  = _read(target_features)
    right = _read(join_features)
    result = _core.spatial_join(left, right, predicate=predicate, how=how)
    _write(result, output)
