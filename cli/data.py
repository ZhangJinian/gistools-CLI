"""
Data Management 工具箱 CLI
基于 Click Group 实现 6 个子命令：
merge / split / feature-to-line / feature-to-polygon / add-field / delete-field
"""
import sys
import click
from pathlib import Path
from core.data_mgmt import (
    merge_vectors,
    split_by_field,
    feature_to_line,
    feature_to_polygon,
    add_field,
    delete_field,
)
from core.formats import RASTER_DRIVERS


def _check_not_raster(path):
    ext = path.suffix.lower()
    if ext in RASTER_DRIVERS:
        raise RuntimeError(
            "gistools data 工具箱仅支持矢量数据（点/线/面）\n"
            "  文件：{} 是栅格格式，无法处理".format(path.name)
        )


@click.group()
def data():
    """Data Management 工具箱 — 矢量数据的合并、分割、类型转换、字段管理"""
    pass


@data.command("merge")
@click.argument("input_files", nargs=-1, required=True, metavar="<input1> <input2> [...] <output>")
@click.option("--encoding", default="UTF-8", help="文件编码（默认 UTF-8）")
def merge(input_files, encoding):
    """合并多个矢量文件为一个文件。"""
    if len(input_files) < 2:
        click.echo("✗ 错误：merge 至少需要两个输入文件")
        sys.exit(1)
    output = Path(input_files[-1])
    inputs = [Path(f) for f in input_files[:-1]]
    for f in inputs:
        if not f.exists():
            click.echo("✗ 错误：输入文件不存在\n  {}".format(f))
            sys.exit(1)
        _check_not_raster(f)
    try:
        count = merge_vectors(inputs, output, encoding=encoding)
        click.echo("✓ 合并完成：{} 个要素 → {}".format(count, output.name))
    except Exception as e:
        click.echo("✗ 合并失败：{}".format(e))
        sys.exit(1)


@data.command("split")
@click.argument("input", metavar="<input>")
@click.argument("output_dir", metavar="<output_dir>")
@click.option("--by", "split_field", required=True, help="用于分割的字段名")
@click.option("--prefix", default="", help="输出文件名前缀")
@click.option("--encoding", default="UTF-8", help="文件编码")
def split(input, output_dir, split_field, prefix, encoding):
    """按字段值将矢量文件分割为多个文件。"""
    input_path = Path(input)
    if not input_path.exists():
        click.echo("✗ 错误：输入文件不存在\n  {}".format(input_path))
        sys.exit(1)
    _check_not_raster(input_path)
    try:
        count = split_by_field(input_path, output_dir, split_field, prefix=prefix, encoding=encoding)
        click.echo("✓ 分割完成：{} 个文件 → {}".format(count, output_dir))
    except Exception as e:
        click.echo("✗ 分割失败：{}".format(e))
        sys.exit(1)


@data.command("feature-to-line")
@click.argument("input", metavar="<input>")
@click.argument("output", metavar="<output>")
@click.option("--encoding", default="UTF-8", help="文件编码")
def feature_to_line_cmd(input, output, encoding):
    """将面/线要素转换为线要素。面要素取外边界线，线要素保持不变。"""
    input_path = Path(input)
    if not input_path.exists():
        click.echo("✗ 错误：输入文件不存在\n  {}".format(input_path))
        sys.exit(1)
    _check_not_raster(input_path)
    try:
        count = feature_to_line(input_path, output, encoding=encoding)
        click.echo("✓ 转换完成：{} 个线要素 → {}".format(count, output))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)


@data.command("feature-to-polygon")
@click.argument("input", metavar="<input>")
@click.argument("output", metavar="<output>")
@click.option("--encoding", default="UTF-8", help="文件编码")
def feature_to_polygon_cmd(input, output, encoding):
    """将线要素转换为面要素（自动闭合开口的线）。"""
    input_path = Path(input)
    if not input_path.exists():
        click.echo("✗ 错误：输入文件不存在\n  {}".format(input_path))
        sys.exit(1)
    _check_not_raster(input_path)
    try:
        count = feature_to_polygon(input_path, output, encoding=encoding)
        click.echo("✓ 转换完成：{} 个面要素 → {}".format(count, output))
    except Exception as e:
        click.echo("✗ 转换失败：{}".format(e))
        sys.exit(1)


@data.command("add-field")
@click.argument("input", metavar="<input>")
@click.argument("output", metavar="<output>")
@click.option("--name", "field_name", required=True, help="新字段名")
@click.option("--type", "field_type", default="STRING", type=click.Choice(["STRING", "INTEGER", "REAL"]), help="字段类型")
@click.option("--value", "default_value", default=None, help="默认值")
@click.option("--encoding", default="UTF-8", help="文件编码")
def add_field_cmd(input, output, field_name, field_type, default_value, encoding):
    """为矢量文件添加新字段。"""
    input_path = Path(input)
    if not input_path.exists():
        click.echo("✗ 错误：输入文件不存在\n  {}".format(input_path))
        sys.exit(1)
    _check_not_raster(input_path)
    if default_value is not None:
        if field_type == "INTEGER":
            try:
                default_value = int(default_value)
            except ValueError:
                click.echo("✗ 错误：INTEGER 类型默认值必须是整数\n  {}".format(default_value))
                sys.exit(1)
        elif field_type == "REAL":
            try:
                default_value = float(default_value)
            except ValueError:
                click.echo("✗ 错误：REAL 类型默认值必须是数值\n  {}".format(default_value))
                sys.exit(1)
    try:
        count = add_field(input_path, output, field_name, field_type, default_value, encoding=encoding)
        click.echo("✓ 添加字段完成：{} 个要素 → {}".format(count, output))
    except Exception as e:
        click.echo("✗ 添加字段失败：{}".format(e))
        sys.exit(1)


@data.command("delete-field")
@click.argument("input", metavar="<input>")
@click.argument("output", metavar="<output>")
@click.option("--name", "field_name", required=True, help="要删除的字段名")
@click.option("--encoding", default="UTF-8", help="文件编码")
def delete_field_cmd(input, output, field_name, encoding):
    """从矢量文件中删除指定字段。"""
    input_path = Path(input)
    if not input_path.exists():
        click.echo("✗ 错误：输入文件不存在\n  {}".format(input_path))
        sys.exit(1)
    _check_not_raster(input_path)
    try:
        count = delete_field(input_path, output, field_name, encoding=encoding)
        click.echo("✓ 删除字段完成：{} 个要素 → {}".format(count, output))
    except ValueError as e:
        click.echo("✗ 错误：{}".format(e))
        sys.exit(1)
    except Exception as e:
        click.echo("✗ 删除字段失败：{}".format(e))
        sys.exit(1)
