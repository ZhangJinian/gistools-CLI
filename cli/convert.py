import sys
from pathlib import Path
import click
from rich.progress import track
from core.formats import detect_format, convert_vector, convert_raster, VECTOR_DRIVERS, RASTER_DRIVERS
from core.batch import collect_input_files, report_errors

ALL_EXTENSIONS = set(VECTOR_DRIVERS) | set(RASTER_DRIVERS)


def _resolve_driver(dst, fmt):
    """返回 (kind, driver)。fmt 优先级高于扩展名。"""
    ext = ".{}".format(fmt.lower()) if fmt else dst.suffix.lower()
    if not ext or ext == ".":
        raise click.UsageError("无法推断目标格式：请指定 --format 或使用带扩展名的输出路径")
    try:
        return detect_format(Path("x" + ext))
    except ValueError:
        raise click.UsageError("不支持的目标格式：{}".format(ext))


def _convert_single(src, dst, fmt, verbose):
    kind, driver = _resolve_driver(dst, fmt)

    # 检测输入格式，矢量→栅格直接拒绝
    try:
        input_kind, _ = detect_format(src)
    except ValueError:
        raise click.UsageError("无法识别输入文件格式：{}".format(src))

    if input_kind == "vector" and kind == "raster":
        raise click.UsageError(
            "不支持将矢量文件转换为栅格格式。\n"
            "  输入：{}（矢量）\n"
            "  输出：{}（栅格）\n"
            "  提示：gistools convert 仅支持矢量↔矢量、栅格↔栅格转换。".format(
                src.name, dst.name
            )
        )
    if input_kind == "raster" and kind == "vector":
        raise click.UsageError(
            "不支持将栅格文件转换为矢量格式。\n"
            "  输入：{}（栅格）\n"
            "  输出：{}（矢量）\n"
            "  提示：gistools convert 仅支持矢量↔矢量、栅格↔栅格转换。".format(
                src.name, dst.name
            )
        )

    if verbose:
        click.echo("转换：{} → {}  [{}]".format(src, dst, driver))
    try:
        if kind == "vector":
            convert_vector(src, dst, driver)
        else:
            convert_raster(src, dst, driver)
        click.echo("✓ {} → {}".format(src.name, dst.name))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)


def _convert_batch(src_dir, dst_dir, fmt, verbose):
    dst_dir.mkdir(parents=True, exist_ok=True)
    files = collect_input_files(src_dir, ALL_EXTENSIONS)

    if not files:
        click.echo("⚠ 未找到可处理的文件，已跳过")
        return

    # 解析目标格式
    if fmt:
        ext = ".{}".format(fmt.lower())
        try:
            target_kind, target_driver = detect_format(Path("x" + ext))
        except ValueError:
            raise click.UsageError("不支持的目标格式：.{}".format(fmt))
    else:
        target_kind = target_driver = None

    # 检查所有输入文件是否与目标格式兼容
    for f in files:
        try:
            input_kind, _ = detect_format(f)
        except ValueError:
            errors.append((f.name, "无法识别格式，跳过"))
            continue
        if target_kind and input_kind != target_kind:
            raise click.UsageError(
                "批量转换中文件格式不一致，无法批量转换。\n"
                "  发现文件：{}（{}）\n"
                "  目标格式：{}\n"
                "  提示：请确保所有输入文件类型相同，或分开处理。".format(
                    f.name, input_kind, fmt or "从扩展名推断"
                )
            )

    errors = []
    success = 0

    for f in (track(files, description="处理中...") if not verbose else files):
        if fmt:
            ext = ".{}".format(fmt.lower())
        else:
            ext = f.suffix.lower()
        dst_file = dst_dir / (f.stem + ext)

        try:
            kind, driver = detect_format(dst_file)
            if kind == "vector":
                convert_vector(f, dst_file, driver)
            else:
                convert_raster(f, dst_file, driver)
            success += 1
            if verbose:
                click.echo("✓ {} → {}".format(f.name, dst_file.name))
        except Exception as e:
            errors.append((f.name, str(e)))
            if verbose:
                click.echo("✗ {} — {}".format(f.name, e))

    click.echo("\n完成：{} 成功 / {} 失败".format(success, len(errors)))
    wrote_log = report_errors(errors, dst_dir / "gistools-errors.log" if errors else None)
    if errors:
        sys.exit(1)


@click.command()
@click.argument("input_path", metavar="<input>", type=click.Path(exists=False))
@click.argument("output_path", metavar="<output>")
@click.option("--format", "fmt", default=None, help="目标格式（geojson/shp/kml/tiff 等）")
@click.option("--verbose", "-v", is_flag=True, help="显示详细处理日志")
@click.option("--dry-run", is_flag=True, help="预览操作，不实际执行")
def convert(input_path, output_path, fmt, verbose, dry_run):
    """矢量/栅格格式互转。<input> 和 <output> 可以是文件或文件夹。"""
    src = Path(input_path)
    dst = Path(output_path)

    if not src.exists():
        click.echo("✗ 错误：输入路径不存在\n  路径：{}".format(src))
        sys.exit(1)

    if src.is_file() and dst.is_dir():
        raise click.UsageError("输入是文件，输出应为文件路径（而非文件夹）")
    if src.is_dir() and dst.exists() and dst.is_file():
        raise click.UsageError("输入是文件夹，输出应为文件夹路径（而非文件）")

    if dry_run:
        if src.is_file():
            kind, driver = _resolve_driver(dst, fmt)
            click.echo("[dry-run] {} → {}  [{}]".format(src.name, dst.name, driver))
        else:
            files = collect_input_files(src, ALL_EXTENSIONS)
            click.echo("[dry-run] 将处理以下文件（共 {} 个）：".format(len(files)))
            for f in files:
                click.echo("  {}".format(f.name))
        return

    if src.is_file():
        _convert_single(src, dst, fmt, verbose)
    else:
        _convert_batch(src, dst, fmt, verbose)
