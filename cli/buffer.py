import sys
from pathlib import Path
import click
from rich.progress import track
from core.formats import detect_format, VECTOR_DRIVERS, RASTER_DRIVERS
from core.spatial import buffer_file
from core.batch import collect_input_files, report_errors
from cli.analysis import analysis


def _check_not_raster(path):
    ext = path.suffix.lower()
    if ext in RASTER_DRIVERS:
        raise RuntimeError(
            "gistools buffer 仅支持矢量数据（点/线/面）\n"
            "  文件：{} 是栅格格式，无法处理".format(path.name)
        )


def _buffer_single(src, dst, distance, unit, dissolve, verbose, dry_run):
    _check_not_raster(src)
    if dry_run:
        click.echo("[dry-run] {} → {}  [buffer {} {}]".format(
            src.name, dst.name, distance, unit))
        return
    try:
        buffer_file(src, dst, distance, unit, dissolve)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 缓冲区计算失败：{}".format(e))
        sys.exit(1)


def _buffer_batch(src_dir, dst_dir, distance, unit, dissolve, verbose, dry_run):
    dst_dir.mkdir(parents=True, exist_ok=True)
    files = collect_input_files(src_dir, set(VECTOR_DRIVERS.keys()))
    if not files:
        click.echo("⚠ 未找到可处理的矢量文件，已跳过")
        return
    errors = []
    success = 0
    for f in (track(files, description="Buffer 中...") if not verbose else files):
        dst_file = dst_dir / f.name
        if dry_run:
            click.echo("[dry-run] {} → {}".format(f.name, dst_file.name))
            continue
        try:
            _check_not_raster(f)
            buffer_file(f, dst_file, distance, unit, dissolve)
            success += 1
            if verbose:
                click.echo("✓ {}".format(f.name))
        except Exception as e:
            errors.append((f.name, str(e)))
            if verbose:
                click.echo("✗ {} — {}".format(f.name, e))
    click.echo("\n完成：{} 成功 / {} 失败".format(success, len(errors)))
    report_errors(errors, dst_dir / "gistools-errors.log" if errors else None)
    if errors:
        sys.exit(1)


@analysis.command()
@click.argument("input_path", metavar="<input>", type=click.Path(exists=False))
@click.argument("output_path", metavar="<output>")
@click.option("--distance", required=True, type=float, help="缓冲距离（必填）")
@click.option("--unit", default="meters",
              type=click.Choice(["meters", "km", "degrees"]),
              help="距离单位（默认 meters）")
@click.option("--dissolve", is_flag=True, help="合并所有缓冲区为单个要素")
@click.option("--verbose", "-v", is_flag=True, help="显示详细处理日志")
@click.option("--dry-run", is_flag=True, help="预览操作，不实际执行")
def buffer(input_path, output_path, distance, unit, dissolve, verbose, dry_run):
    """缓冲区分析（仅限矢量数据）。<input> 和 <output> 可以是文件或文件夹。"""
    src = Path(input_path)
    dst = Path(output_path)

    if not src.exists():
        click.echo("✗ 错误：输入路径不存在\n  路径：{}".format(src))
        sys.exit(1)

    if src.is_file() and dst.is_dir():
        raise click.UsageError("输入是文件，输出应为文件路径")
    if src.is_dir() and dst.exists() and dst.is_file():
        raise click.UsageError("输入是文件夹，输出应为文件夹路径")

    if src.is_file():
        _buffer_single(src, dst, distance, unit, dissolve, verbose, dry_run)
    else:
        _buffer_batch(src, dst, distance, unit, dissolve, verbose, dry_run)
