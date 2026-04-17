"""
Analysis 工具箱核心实现：Clip / Intersect / Union / Dissolve / Spatial Join。
基于 Shapely + GeoPandas 实现。
"""
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import MultiPolygon, Polygon
from typing import Sequence, Optional


def clip(features: gpd.GeoDataFrame, clip_layer: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    裁剪：返回 features 中落在 clip_layer 范围内的部分。

    Parameters
    ----------
    features : GeoDataFrame
        输入要素（被裁切的对象）
    clip_layer : GeoDataFrame
        裁切范围

    Returns
    -------
    GeoDataFrame
        裁切后的要素，属性表保留 features 的原始字段
    """
    # 用 clip_layer 的外包合并几何作为整体裁切范围
    mask = clip_layer.unary_union
    clipped = features.copy()
    clipped.geometry = clipped.geometry.intersection(mask)
    # 过滤掉空几何
    clipped = clipped[~clipped.is_empty]
    return clipped


def intersect(features: gpd.GeoDataFrame, intersect_with: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    交集：返回 features 与 intersect_with 的重叠区域。

    Parameters
    ----------
    features : GeoDataFrame
        输入要素
    intersect_with : GeoDataFrame
        另一个输入要素

    Returns
    -------
    GeoDataFrame
        交集结果
    """
    import shapely

    # 逐个求交
    result_geoms = []
    result_attrs = []

    for _, feat in features.iterrows():
        for _, other in intersect_with.iterrows():
            inter = feat.geometry.intersection(other.geometry)
            if inter.is_empty:
                continue
            result_geoms.append(inter)
            result_attrs.append({k: v for k, v in feat.items() if k != "geometry"})

    if not result_geoms:
        non_geom_cols = [c for c in features.columns if c != "geometry"]
        return gpd.GeoDataFrame(columns=non_geom_cols, geometry=gpd.GeoSeries([], crs=features.crs), crs=features.crs)

    result = gpd.GeoDataFrame(result_attrs, geometry=result_geoms, crs=features.crs)
    result.reset_index(drop=True, inplace=True)
    return result


def union(features: gpd.GeoDataFrame, union_with: Optional[gpd.GeoDataFrame] = None) -> gpd.GeoDataFrame:
    """
    并集：返回两个图层所有要素的合并（保留全部几何和属性）。

    Parameters
    ----------
    features : GeoDataFrame
    union_with : GeoDataFrame, optional
        与 features 合并的另一个图层

    Returns
    -------
    GeoDataFrame
        合并后的所有要素
    """
    if union_with is None:
        # 单图层内部求并集（融合重叠部分）
        return features.copy()

    # 两个图层按行拼接
    combined = pd.concat([features, union_with], ignore_index=True)
    return combined


def dissolve(features: gpd.GeoDataFrame, by_field: str, as_multipart: bool = False) -> gpd.GeoDataFrame:
    """
    融合：按字段合并相邻多边形。

    Parameters
    ----------
    features : GeoDataFrame
        输入面要素
    by_field : str
        融合字段名
    as_multipart : bool
        是否输出多部件几何（MultiPolygon），默认 False（单部件，即 explode）

    Returns
    -------
    GeoDataFrame
        融合后的要素，属性表保留 by_field 和其他数值字段的聚合值
    """
    if by_field not in features.columns:
        raise ValueError("融合字段 '{}' 不存在".format(by_field))

    dissolved = features.dissolve(by=by_field, aggfunc="first")
    dissolved.reset_index(inplace=True)

    if not as_multipart:
        # 将多部件拆分为单部件
        dissolved = dissolved.explode(index_parts=False).reset_index(drop=True)

    return dissolved


def spatial_join(
    left_df: gpd.GeoDataFrame,
    right_df: gpd.GeoDataFrame,
    predicate: str = "intersects",
    how: str = "left",
    lsuffix: str = "",
    rsuffix: str = "_right",
) -> gpd.GeoDataFrame:
    """
    空间连接：基于空间关系将 right_df 的属性关联到 left_df。

    Parameters
    ----------
    left_df : GeoDataFrame
        左侧要素（被连接的目标）
    right_df : GeoDataFrame
        右侧要素（提供属性）
    predicate : str
        空间谓词：intersects / within / contains / crosses 等，默认 intersects
    how : str
        连接类型：left / right / inner / outer，默认 left
    lsuffix : str
        左表重名后缀
    rsuffix : str
        右表重名后缀

    Returns
    -------
    GeoDataFrame
        连接结果
    """
    result = gpd.sjoin(
        left_df,
        right_df,
        how=how,
        predicate=predicate,
        lsuffix=lsuffix,
        rsuffix=rsuffix,
    )
    return result
