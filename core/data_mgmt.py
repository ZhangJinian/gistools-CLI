"""
Data Management 核心实现
基于 GeoPandas 实现矢量数据的合并、分割、类型转换、字段管理
"""
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import LineString, Polygon


def merge_vectors(input_files, output, encoding="UTF-8"):
    """
    合并多个矢量文件为一个文件。

    参数:
        input_files: 输入文件路径列表
        output: 输出文件路径
        encoding: 文件编码，默认 UTF-8
    """
    gdfs = [gpd.read_file(str(f), encoding=encoding) for f in input_files]
    result = pd.concat(gdfs, ignore_index=True)
    _ensure_output_dir(output)
    result.to_file(str(output), encoding=encoding)
    return len(result)


def split_by_field(input_file, output_dir, split_field, prefix="", encoding="UTF-8"):
    """
    按字段值分割矢量文件为多个文件。

    参数:
        input_file: 输入文件路径
        output_dir: 输出目录
        split_field: 用于分割的字段名
        prefix: 输出文件名前缀
        encoding: 文件编码，默认 UTF-8
    返回:
        分割产生的文件数量
    """
    gdf = gpd.read_file(str(input_file), encoding=encoding)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for value, group in gdf.groupby(split_field):
        safe_value = str(value).replace("/", "_").replace("\\", "_")
        out_name = f"{prefix}{safe_value}.shp" if prefix else f"{safe_value}.shp"
        group.to_file(str(output_dir / out_name), encoding=encoding)
        count += 1
    return count


def feature_to_line(input_file, output, encoding="UTF-8"):
    """
    将面/线要素转换为线要素。
    面要素取其外边界线；线要素保持不变。

    参数:
        input_file: 输入文件路径
        output: 输出文件路径
        encoding: 文件编码，默认 UTF-8
    返回:
        转换后的要素数量
    """
    gdf = gpd.read_file(str(input_file), encoding=encoding)

    def to_line(geom):
        # 如果是面要素，取外边界；线要素直接返回
        if hasattr(geom, "exterior"):
            return LineString(geom.exterior.coords)
        return geom

    gdf.geometry = gdf.geometry.apply(to_line)
    _ensure_output_dir(output)
    gdf.to_file(str(output), encoding=encoding)
    return len(gdf)


def feature_to_polygon(input_file, output, encoding="UTF-8"):
    """
    将线要素转换为面要素（自动闭合开口的线）。

    参数:
        input_file: 输入文件路径
        output: 输出文件路径
        encoding: 文件编码，默认 UTF-8
    返回:
        转换后的要素数量
    """
    gdf = gpd.read_file(str(input_file), encoding=encoding)

    def to_polygon(geom):
        if geom.is_closed:
            return Polygon(geom.coords)
        else:
            # 闭合开口的线：首尾点相连
            coords = list(geom.coords)
            return Polygon(coords + [coords[0]])

    gdf.geometry = gdf.geometry.apply(to_polygon)
    _ensure_output_dir(output)
    gdf.to_file(str(output), encoding=encoding)
    return len(gdf)


def add_field(input_file, output, field_name, field_type="STRING", default_value=None, encoding="UTF-8"):
    """
    为矢量文件添加新字段。

    参数:
        input_file: 输入文件路径
        output: 输出文件路径
        field_name: 字段名
        field_type: 字段类型，STRING | INTEGER | REAL
        default_value: 默认值，未指定时根据类型推断（0 或空字符串）
        encoding: 文件编码，默认 UTF-8
    返回:
        要素数量
    """
    gdf = gpd.read_file(str(input_file), encoding=encoding)

    # 根据类型设置默认值
    if default_value is not None:
        value = default_value
    elif field_type == "INTEGER":
        value = 0
    elif field_type == "REAL":
        value = 0.0
    else:
        value = ""

    gdf[field_name] = value
    _ensure_output_dir(output)
    gdf.to_file(str(output), encoding=encoding)
    return len(gdf)


def delete_field(input_file, output, field_name, encoding="UTF-8"):
    """
    从矢量文件中删除指定字段。

    参数:
        input_file: 输入文件路径
        output: 输出文件路径
        field_name: 要删除的字段名
        encoding: 文件编码，默认 UTF-8
    返回:
        要素数量
    """
    gdf = gpd.read_file(str(input_file), encoding=encoding)
    if field_name not in gdf.columns:
        raise ValueError(f"字段不存在：{field_name}")
    gdf.drop(columns=[field_name], inplace=True)
    _ensure_output_dir(output)
    gdf.to_file(str(output), encoding=encoding)
    return len(gdf)


def _ensure_output_dir(output_path):
    """确保输出文件的父目录存在"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
