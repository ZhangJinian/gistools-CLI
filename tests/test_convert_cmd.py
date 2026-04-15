import pytest
from click.testing import CliRunner
from cli.main import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_convert_single_file(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "convert",
        str(sample_dir / "points.shp"),
        str(tmp_path / "out.geojson"),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "out.geojson").exists()

def test_convert_infers_format_from_extension(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "convert",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.shp"),
    ])
    assert result.exit_code == 0

def test_convert_explicit_format_wins(runner, sample_dir, tmp_path):
    """--format 优先级高于输出扩展名"""
    result = runner.invoke(cli, [
        "convert",
        str(sample_dir / "points.shp"),
        str(tmp_path / "out.geojson"),
        "--format", "geojson",
    ])
    assert result.exit_code == 0

def test_convert_missing_input(runner, tmp_path):
    result = runner.invoke(cli, [
        "convert",
        str(tmp_path / "notexist.shp"),
        str(tmp_path / "out.geojson"),
    ])
    assert result.exit_code == 1
    assert "不存在" in result.output

def test_convert_batch_folder(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "convert",
        str(sample_dir),
        str(tmp_path),
        "--format", "geojson",
    ])
    assert result.exit_code in (0, 1)
    assert "成功" in result.output

def test_convert_batch_empty_folder(runner, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    result = runner.invoke(cli, ["convert", str(empty), str(out), "--format", "geojson"])
    assert result.exit_code == 0
    assert "未找到" in result.output

def test_convert_mismatched_types_file_to_folder(runner, sample_dir, tmp_path):
    """input 是文件，output 是已存在的文件夹 → 报错"""
    result = runner.invoke(cli, [
        "convert",
        str(sample_dir / "points.shp"),
        str(tmp_path),  # 已存在的文件夹
    ])
    assert result.exit_code == 2

def test_convert_no_format_no_extension(runner, sample_dir, tmp_path):
    """output 无扩展名且未指定 --format → 报错"""
    result = runner.invoke(cli, [
        "convert",
        str(sample_dir / "points.shp"),
        str(tmp_path / "out"),
    ])
    assert result.exit_code == 2
