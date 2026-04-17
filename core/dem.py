"""
DEM 栅格分析核心模块 — 基于 GDAL DEMProcessing。
支持：坡度、坡向、山体阴影、等高线生成。
"""
import subprocess
from osgeo import gdal
from pathlib import Path


def calculate_slope(dem_path, output_path, unit="DEGREE", scale=1.0):
    """
    坡度分析。

    Parameters
    ----------
    dem_path : str or Path
        输入 DEM 栅格路径。
    output_path : str or Path
        输出坡度栅格路径。
    unit : str
        'DEGREE'（度，默认）或 'PERCENT'（百分比）。
    scale : float
        Z 因子，默认为 1.0。
    """
    dem_path = str(dem_path)
    output_path = str(output_path)
    ds = gdal.Open(dem_path)

    if unit == "PERCENT":
        # zFactor approach gives percent slope (approximate conversion)
        gdal.DEMProcessing(output_path, ds, "slope", zFactor=111120.0, slopeFormat="percent")
    else:
        gdal.DEMProcessing(output_path, ds, "slope", scale=1.0, slopeFormat="degree")
    ds = None
    return output_path


def calculate_aspect(dem_path, output_path):
    """
    坡向分析。

    Parameters
    ----------
    dem_path : str or Path
        输入 DEM 栅格路径。
    output_path : str or Path
        输出坡向栅格路径（度为单位，0=北，90=东，180=南，270=西）。
    """
    dem_path = str(dem_path)
    output_path = str(output_path)
    ds = gdal.Open(dem_path)

    gdal.DEMProcessing(output_path, ds, "aspect")
    ds = None
    return output_path


def calculate_hillshade(dem_path, output_path, azimuth=315, altitude=45, scale=1.0):
    """
    山体阴影。

    Parameters
    ----------
    dem_path : str or Path
        输入 DEM 栅格路径。
    output_path : str or Path
        输出山体阴影栅格路径。
    azimuth : float
        方位角（光源方向），默认 315 度。
    altitude : float
        高度角（光源高度），默认 45 度。
    scale : float
        Z 因子，默认 1.0。
    """
    dem_path = str(dem_path)
    output_path = str(output_path)
    ds = gdal.Open(dem_path)

    gdal.DEMProcessing(
        output_path, ds, "hillshade",
        azimuth=azimuth, altitude=altitude, zFactor=scale
    )
    ds = None
    return output_path


def generate_contour(dem_path, output_path, interval, start=0, field="ELEV"):
    """
    等高线生成。

    Parameters
    ----------
    dem_path : str or Path
        输入 DEM 栅格路径。
    output_path : str or Path
        输出矢量等高线文件路径（GeoJSON）。
    interval : float
        等高线间距（必填）。
    start : float
        起始值，默认 0。
    field : str
        高程字段名，默认 "ELEV"。
    """
    dem_path = str(dem_path)
    output_path = str(output_path)

    # Use gdal_contour CLI directly (DEMProcessing options have compatibility issues)
    cmd = [
        "gdal_contour",
        "-a", field,
        "-i", str(interval),
        "-off", str(start),
        "-f", "GeoJSON",
        dem_path,
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Filter out harmless DLL warnings from stderr
        stderr_lines = [
            line for line in result.stderr.splitlines()
            if "DLL" not in line and line.strip()
        ]
        error_msg = "\n".join(stderr_lines) if stderr_lines else result.stderr
        raise RuntimeError(
            "gdal_contour failed (return code {}):\n{}".format(
                result.returncode, error_msg
            )
        )
    return output_path
