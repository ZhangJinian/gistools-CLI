import sys
from pathlib import Path
import click
import geopandas as gpd
from rich.progress import track
from core.crs import resolve_crs
from core.formats import VECTOR_DRIVERS
from core.batch import collect_input_files, report_errors


def _reproject_file(src, dst, to_crs, from_crs_name, verbose):
    gdf = gpd.read_file(str(src))
    if from_crs_name:
        gdf = gdf.set_crs(resolve_crs(from_crs_name), allow_override=True)
    elif gdf.crs is None:
        raise RuntimeError(
            "文件无坐标系信息（缺少 .prj 或 crs 字段）\n"
            "  请使用 --from 参数手动指定，例如：--from EPSG:4326 或 --from WGS84"
        )
    result = gdf.to_crs(to_crs)
    dst.parent.mkdir(parents=True, exist_ok=True)
    ext = dst.suffix.lower()
    driver = VECTOR_DRIVERS.get(ext, "GeoJSON")
    result.to_file(str(dst), driver=driver)
    if verbose:
        click.echo("✓ {} → {}  [{} → {}]".format(src.name, dst.name, gdf.crs, to_crs))


@click.command()
@click.argument("input_path", metavar="<input>", type=click.Path(exists=False))
@click.argument("output_path", metavar="<output>")
@click.option("--to", "to_crs_name", required=True, help="目标坐标系")
@click.option("--from", "from_crs_name", default=None, help="源坐标系（可选，未指定时从文件读取）")
@click.option("--verbose", "-v", is_flag=True, help="显示详细处理日志")
@click.option("--dry-run", is_flag=True, help="预览操作，不实际执行")
def reproject(input_path, output_path, to_crs_name, from_crs_name, verbose, dry_run):
    """坐标系转换。<input> 和 <output> 可以是文件或文件夹。"""
    src = Path(input_path)
    dst = Path(output_path)

    if not src.exists():
        click.echo("✗ 错误：输入路径不存在\n  路径：{}".format(src))
        sys.exit(1)

    if src.is_file() and dst.is_dir():
        raise click.UsageError("输入是文件，输出应为文件路径")
    if src.is_dir() and dst.exists() and dst.is_file():
        raise click.UsageError("输入是文件夹，输出应为文件夹路径")

    try:
        to_crs = resolve_crs(to_crs_name)
    except ValueError as e:
        click.echo("✗ {}".format(e))
        sys.exit(1)

    if src.is_file():
        if dry_run:
            click.echo("[dry-run] {} → {}  [→ {}]".format(src.name, dst.name, to_crs_name))
            return
        try:
            _reproject_file(src, dst, to_crs, from_crs_name, verbose)
            if not verbose:
                click.echo("✓ {} → {}".format(src.name, dst.name))
        except Exception as e:
            click.echo("✗ {}".format(e))
            sys.exit(1)
    else:
        dst.mkdir(parents=True, exist_ok=True)
        files = collect_input_files(src, set(VECTOR_DRIVERS.keys()))
        if not files:
            click.echo("⚠ 未找到可处理的矢量文件，已跳过")
            return
        errors = []
        success = 0
        for f in (track(files, description="转投影中...") if not verbose else files):
            dst_file = dst / f.name
            if dry_run:
                click.echo("[dry-run] {} → {}".format(f.name, dst_file.name))
                continue
            try:
                _reproject_file(f, dst_file, to_crs, from_crs_name, verbose)
                success += 1
            except Exception as e:
                errors.append((f.name, str(e)))
        click.echo("\n完成：{} 成功 / {} 失败".format(success, len(errors)))
        report_errors(errors, dst / "gistools-errors.log" if errors else None)
        if errors:
            sys.exit(1)
