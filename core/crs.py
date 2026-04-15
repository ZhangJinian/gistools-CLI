from pyproj import CRS

CRS_ALIASES = {
    "WGS84": "EPSG:4326",
    "CGCS2000": "EPSG:4490",
    "国家2000": "EPSG:4490",
    "北京54": "EPSG:4214",
    "西安80": "EPSG:4610",
    "GCJ02": "EPSG:4326",  # GCJ-02 无标准 EPSG，此处先映射 WGS84
}


def resolve_crs(name):
    """
    将用户输入的坐标系名称（EPSG 编码/英文别名/中文别名）解析为 pyproj.CRS。
    无法识别时抛 ValueError，含"无法识别"。
    """
    key = name.strip()
    mapped = CRS_ALIASES.get(key, key)
    # 纯数字视为 EPSG 编码
    if mapped.isdigit():
        mapped = "EPSG:{}".format(mapped)
    try:
        return CRS.from_user_input(mapped)
    except Exception:
        raise ValueError(
            "无法识别的坐标系：{}\n请使用 EPSG 编码（如 EPSG:4326）或别名（如 WGS84、CGCS2000、国家2000）".format(name)
        )
