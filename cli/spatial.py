import sys
from pathlib import Path
import click
from core.dem import calculate_slope, calculate_aspect, calculate_hillshade, generate_contour
from core.formats import detect_format

@click.group()
def spatial():
    """Spatial Analyst 工具箱（坡度 / 坡向 / 山体阴影 / 等高线）"""
    pass

@spatial.command("slope")
@click.argument("input_dem", metavar="<input_dem>", type=click.Path(exists=True))
@click.argument("output_slope", metavar="<output_slope>", type=click.Path(exists=False))
@click.option("--unit", type=click.Choice(["DEGREE", "PERCENT"], case_sensitive=False), default="DEGREE", help="坡度单位（默认 DEGREE）")
@click.option("--scale", type=float, default=1.0, help="Z 因子，默认 1.0")
def slope(input_dem, output_slope, unit, scale):
    src = Path(input_dem)
    dst = Path(output_slope)
    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "raster":
        click.echo("✗ 输入不是栅格文件：{}".format(src))
        sys.exit(1)
    try:
        calculate_slope(src, dst, unit=unit, scale=scale)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 坡度分析失败：{}".format(e))
        sys.exit(1)

@spatial.command("aspect")
@click.argument("input_dem", metavar="<input_dem>", type=click.Path(exists=True))
@click.argument("output_aspect", metavar="<output_aspect>", type=click.Path(exists=False))
def aspect(input_dem, output_aspect):
    src = Path(input_dem)
    dst = Path(output_aspect)
    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "raster":
        click.echo("✗ 输入不是栅格文件：{}".format(src))
        sys.exit(1)
    try:
        calculate_aspect(src, dst)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 坡向分析失败：{}".format(e))
        sys.exit(1)

@spatial.command("hillshade")
@click.argument("input_dem", metavar="<input_dem>", type=click.Path(exists=True))
@click.argument("output_hillshade", metavar="<output_hillshade>", type=click.Path(exists=False))
@click.option("--azimuth", type=float, default=315, help="方位角（光源方向），默认 315")
@click.option("--altitude", type=float, default=45, help="高度角（光源高度），默认 45")
@click.option("--scale", type=float, default=1.0, help="Z 因子，默认 1.0")
def hillshade(input_dem, output_hillshade, azimuth, altitude, scale):
    src = Path(input_dem)
    dst = Path(output_hillshade)
    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "raster":
        click.echo("✗ 输入不是栅格文件：{}".format(src))
        sys.exit(1)
    try:
        calculate_hillshade(src, dst, azimuth=azimuth, altitude=altitude, scale=scale)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 山体阴影生成失败：{}".format(e))
        sys.exit(1)

@spatial.command("contour")
@click.argument("input_dem", metavar="<input_dem>", type=click.Path(exists=True))
@click.argument("output_contour", metavar="<output_contour>", type=click.Path(exists=False))
@click.option("--interval", type=float, required=True, help="等高线间距（必填）")
@click.option("--start", type=float, default=0, help="起始值，默认 0")
@click.option("--field", type=str, default="ELEV", help="高程字段名，默认 ELEV")
def contour(input_dem, output_contour, interval, start, field):
    src = Path(input_dem)
    dst = Path(output_contour)
    try:
        kind, _ = detect_format(src)
    except ValueError:
        click.echo("✗ 无法识别输入文件格式：{}".format(src))
        sys.exit(1)
    if kind != "raster":
        click.echo("✗ 输入不是栅格文件：{}".format(src))
        sys.exit(1)
    try:
        generate_contour(src, dst, interval=interval, start=start, field=field)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 等高线生成失败：{}".format(e))
        sys.exit(1)
