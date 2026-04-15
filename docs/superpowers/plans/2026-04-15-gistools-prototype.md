# GISTools CLI Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `gistools convert`、`gistools reproject`、`gistools buffer` 三个 CLI 命令，支持单文件和批量文件夹处理，附带完整错误报告。

**Architecture:** CLI 层（click）负责命令注册和参数解析，core 层负责实际 GIS 业务逻辑，两层通过清晰的函数接口分离。批量处理逻辑统一在 `core/batch.py` 中，避免三个命令各自重复实现。

**Tech Stack:** Python 3.10+（conda pytorch 环境）、GDAL/OGR（已有）、pyproj、Shapely 2.x、GeoPandas、Click 8.x、rich

**Spec:** `docs/2026-04-15-gistools-design.md`

---

## 文件结构

```
gistools/
├── cli/
│   ├── __init__.py          # 空
│   ├── main.py              # click group 入口
│   ├── convert.py           # gistools convert 命令
│   ├── reproject.py         # gistools reproject 命令
│   └── buffer.py            # gistools buffer 命令
├── core/
│   ├── __init__.py          # 空
│   ├── formats.py           # 格式检测、单文件矢量/栅格转换
│   ├── crs.py               # 坐标系别名字典 + resolve_crs()
│   ├── spatial.py           # buffer 计算
│   └── batch.py             # 批量处理基础设施（错误收集/汇报）
├── tests/
│   ├── conftest.py          # 共享 fixtures（临时样本数据）
│   ├── test_formats.py      # formats.py 单元测试
│   ├── test_crs.py          # crs.py 单元测试
│   ├── test_spatial.py      # spatial.py 单元测试
│   ├── test_convert_cmd.py  # convert 命令集成测试
│   ├── test_reproject_cmd.py
│   └── test_buffer_cmd.py
├── pyproject.toml
└── docs/
```

---

## Task 0: 环境验证 + 项目骨架

**Files:**
- Create: `pyproject.toml`
- Create: `cli/__init__.py`, `cli/main.py`
- Create: `core/__init__.py`

- [ ] **Step 1: 验证 GDAL 可用**

```bash
conda activate pytorch
python -c "from osgeo import ogr, gdal; print('GDAL OK:', gdal.__version__)"
```

期望输出：`GDAL OK: 3.x.x`（版本号不限）

- [ ] **Step 2: 安装其余依赖**

```bash
conda activate pytorch
pip install click>=8.0 rich>=13.0 geopandas>=0.14 shapely>=2.0 pyproj>=3.0 pytest
```

- [ ] **Step 3: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "gistools"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "geopandas>=0.14",
    "shapely>=2.0",
    "pyproj>=3.0",
]

[project.scripts]
gistools = "cli.main:cli"
```

- [ ] **Step 4: 创建 CLI 入口**

创建 `cli/__init__.py`（空文件）和 `cli/main.py`：

```python
import click

@click.group()
def cli():
    """GISTools — GIS 操作命令行工具包"""
    pass
```

- [ ] **Step 5: 创建 core 空模块**

```bash
touch core/__init__.py
```

- [ ] **Step 6: 可编辑模式安装 + 验证入口**

```bash
pip install -e .
gistools --help
```

期望输出：
```
Usage: gistools [OPTIONS] COMMAND [ARGS]...

  GISTools — GIS 操作命令行工具包

Options:
  --help  Show this message and exit.
```

- [ ] **Step 7: Commit**

```bash
git init
git add pyproject.toml cli/ core/
git commit -m "chore: 项目骨架 + CLI 入口"
```

---

## Task 1: 格式检测与单文件转换（core/formats.py）

**Files:**
- Create: `core/formats.py`
- Create: `tests/conftest.py`
- Create: `tests/test_formats.py`

- [ ] **Step 1: 创建 tests/conftest.py（共享样本数据 fixtures）**

```python
import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString
from pathlib import Path

@pytest.fixture(scope="session")
def sample_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("sample")

    # WGS84 点要素 GeoJSON
    gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    ).to_file(d / "points.geojson", driver="GeoJSON")

    # WGS84 点要素 SHP
    gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    ).to_file(d / "points.shp")

    # 线要素 GeoJSON
    gpd.GeoDataFrame(
        {"name": ["road"]},
        geometry=[LineString([(114.0, 22.5), (114.1, 22.6)])],
        crs="EPSG:4326",
    ).to_file(d / "line.geojson", driver="GeoJSON")

    return d
```

- [ ] **Step 2: 写失败测试**

创建 `tests/test_formats.py`：

```python
import pytest
from pathlib import Path
from core.formats import detect_format, convert_vector, VECTOR_DRIVERS

def test_detect_geojson():
    kind, driver = detect_format(Path("foo.geojson"))
    assert kind == "vector"
    assert driver == "GeoJSON"

def test_detect_shp():
    kind, driver = detect_format(Path("foo.shp"))
    assert kind == "vector"
    assert driver == "ESRI Shapefile"

def test_detect_tiff():
    kind, driver = detect_format(Path("foo.tif"))
    assert kind == "raster"
    assert driver == "GTiff"

def test_detect_unsupported():
    with pytest.raises(ValueError, match="不支持的格式"):
        detect_format(Path("foo.xyz"))

def test_convert_vector_shp_to_geojson(sample_dir, tmp_path):
    src = sample_dir / "points.shp"
    dst = tmp_path / "out.geojson"
    convert_vector(src, dst, "GeoJSON")
    assert dst.exists()
    import geopandas as gpd
    gdf = gpd.read_file(dst)
    assert len(gdf) == 2

def test_convert_vector_geojson_to_shp(sample_dir, tmp_path):
    src = sample_dir / "points.geojson"
    dst = tmp_path / "out.shp"
    convert_vector(src, dst, "ESRI Shapefile")
    assert dst.exists()

def test_convert_vector_overwrite(sample_dir, tmp_path):
    """同名文件自动覆盖，不报错"""
    src = sample_dir / "points.geojson"
    dst = tmp_path / "out.geojson"
    convert_vector(src, dst, "GeoJSON")
    convert_vector(src, dst, "GeoJSON")  # 第二次不应报错
    assert dst.exists()
```

- [ ] **Step 3: 运行确认测试失败**

```bash
cd D:\zjn\code\gistools
conda activate pytorch
pytest tests/test_formats.py -v
```

期望：`ModuleNotFoundError: No module named 'core.formats'`

- [ ] **Step 4: 实现 core/formats.py**

```python
from pathlib import Path
from osgeo import ogr, gdal

VECTOR_DRIVERS: dict[str, str] = {
    ".shp": "ESRI Shapefile",
    ".geojson": "GeoJSON",
    ".kml": "KML",
    ".gml": "GML",
    ".gpkg": "GPKG",
    ".csv": "CSV",
}

RASTER_DRIVERS: dict[str, str] = {
    ".tif": "GTiff",
    ".tiff": "GTiff",
    ".img": "HFA",
    ".hdf": "HDF4",
    ".nc": "netCDF",
}


def detect_format(path: Path) -> tuple[str, str]:
    """返回 ('vector'|'raster', driver_name)，格式不支持则抛 ValueError。"""
    ext = path.suffix.lower()
    if ext in VECTOR_DRIVERS:
        return "vector", VECTOR_DRIVERS[ext]
    if ext in RASTER_DRIVERS:
        return "raster", RASTER_DRIVERS[ext]
    raise ValueError(f"不支持的格式：{ext}")


def convert_vector(src: Path, dst: Path, driver: str) -> None:
    """矢量格式转换，dst 已存在时自动覆盖。"""
    src_ds = ogr.Open(str(src))
    if src_ds is None:
        raise RuntimeError(f"无法读取文件：{src}\n请确认文件完整（SHP 需要 .dbf / .prj 同目录）")
    drv = ogr.GetDriverByName(driver)
    if drv is None:
        raise RuntimeError(f"GDAL 不支持驱动：{driver}")
    if dst.exists():
        drv.DeleteDataSource(str(dst))
    out_ds = drv.CopyDataSource(src_ds, str(dst))
    if out_ds is None:
        raise RuntimeError(f"写出失败：{dst}")
    out_ds.FlushCache()
    out_ds = None
    src_ds = None


def convert_raster(src: Path, dst: Path, driver: str) -> None:
    """栅格格式转换，dst 已存在时自动覆盖。"""
    src_ds = gdal.Open(str(src))
    if src_ds is None:
        raise RuntimeError(f"无法读取栅格文件：{src}")
    if dst.exists():
        dst.unlink()
    drv = gdal.GetDriverByName(driver)
    if drv is None:
        raise RuntimeError(f"GDAL 不支持驱动：{driver}")
    out_ds = drv.CreateCopy(str(dst), src_ds)
    if out_ds is None:
        raise RuntimeError(f"栅格写出失败：{dst}")
    out_ds.FlushCache()
    out_ds = None
    src_ds = None
```

- [ ] **Step 5: 运行确认测试通过**

```bash
pytest tests/test_formats.py -v
```

期望：所有测试 PASS

- [ ] **Step 6: Commit**

```bash
git add core/formats.py tests/conftest.py tests/test_formats.py
git commit -m "feat: 格式检测与单文件矢量/栅格转换"
```

---

## Task 2: 批量处理基础设施（core/batch.py）

**Files:**
- Create: `core/batch.py`

这个模块被 convert / reproject / buffer 三个命令共用，只写一次。

- [ ] **Step 1: 写失败测试**

在 `tests/test_formats.py` 末尾追加：

```python
from core.batch import collect_input_files, report_errors

def test_collect_input_files(sample_dir):
    files = collect_input_files(sample_dir, {".geojson", ".shp"})
    exts = {f.suffix for f in files}
    assert ".geojson" in exts
    assert ".shp" in exts

def test_collect_input_files_empty(tmp_path):
    files = collect_input_files(tmp_path, {".geojson"})
    assert files == []

def test_report_errors_few(capsys):
    errors = [("a.shp", "缺少.prj"), ("b.shp", "文件损坏")]
    wrote_log = report_errors(errors, log_path=None)
    captured = capsys.readouterr()
    assert "a.shp" in captured.out
    assert wrote_log is False

def test_report_errors_many(tmp_path, capsys):
    errors = [(f"file_{i:02d}.shp", "错误") for i in range(15)]
    log = tmp_path / "gistools-errors.log"
    wrote_log = report_errors(errors, log_path=log)
    captured = capsys.readouterr()
    assert "还有" in captured.out
    assert log.exists()
    assert wrote_log is True
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_formats.py::test_collect_input_files -v
```

期望：`ImportError`

- [ ] **Step 3: 实现 core/batch.py**

```python
from pathlib import Path


def collect_input_files(folder: Path, extensions: set[str]) -> list[Path]:
    """返回 folder 下所有扩展名在 extensions 中的文件（不递归子文件夹）。"""
    return [f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix.lower() in extensions]


def report_errors(errors: list[tuple[str, str]], log_path: Path | None) -> bool:
    """
    打印失败汇总。
    - errors: [(filename, reason), ...]
    - log_path: 当 errors > 10 时写入的日志路径（传 None 则强制终端输出）
    返回是否写了 log 文件。
    """
    if not errors:
        return False

    THRESHOLD = 10
    print()  # 空行分隔
    if len(errors) <= THRESHOLD or log_path is None:
        print("失败文件：")
        for name, reason in errors:
            print(f"  · {name} — {reason}")
        return False
    else:
        print(f"失败文件（前 {THRESHOLD} 条）：")
        for name, reason in errors[:THRESHOLD]:
            print(f"  · {name} — {reason}")
        remaining = len(errors) - THRESHOLD
        print(f"  （还有 {remaining} 条，完整列表见 {log_path}）")
        log_path.write_text(
            "\n".join(f"{name}\t{reason}" for name, reason in errors),
            encoding="utf-8",
        )
        return True
```

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/test_formats.py -v
```

期望：全部 PASS

- [ ] **Step 5: Commit**

```bash
git add core/batch.py tests/test_formats.py
git commit -m "feat: 批量处理基础设施（文件收集 + 错误汇报）"
```

---

## Task 3: gistools convert 命令

**Files:**
- Create: `cli/convert.py`
- Modify: `cli/main.py`
- Create: `tests/test_convert_cmd.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_convert_cmd.py`：

```python
import pytest
from click.testing import CliRunner
from cli.main import cli
from pathlib import Path

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
    assert result.exit_code in (0, 1)  # 0 全成功，1 部分失败
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
    """input 是文件，output 是文件夹 → 报错"""
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
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_convert_cmd.py -v
```

期望：`No such command 'convert'`

- [ ] **Step 3: 实现 cli/convert.py**

```python
import sys
from pathlib import Path
import click
from rich.progress import track
from core.formats import detect_format, convert_vector, convert_raster, VECTOR_DRIVERS, RASTER_DRIVERS
from core.batch import collect_input_files, report_errors

ALL_EXTENSIONS = set(VECTOR_DRIVERS) | set(RASTER_DRIVERS)


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

    # 输入存在性检查
    if not src.exists():
        click.echo(f"✗ 错误：输入路径不存在\n  路径：{src}")
        sys.exit(1)

    # 输入/输出类型一致性
    if src.is_file() and dst.is_dir():
        raise click.UsageError("输入是文件，输出应为文件路径（而非文件夹）")
    if src.is_dir() and dst.exists() and dst.is_file():
        raise click.UsageError("输入是文件夹，输出应为文件夹路径（而非文件）")

    if src.is_file():
        _convert_single(src, dst, fmt, verbose, dry_run)
    else:
        _convert_batch(src, dst, fmt, verbose, dry_run)


def _resolve_driver(dst: Path, fmt: str | None) -> tuple[str, str]:
    """返回 (kind, driver)。fmt 优先级高于扩展名。"""
    ext = f".{fmt.lower()}" if fmt else dst.suffix.lower()
    if not ext or ext == ".":
        raise click.UsageError("无法推断目标格式：请指定 --format 或使用带扩展名的输出路径")
    try:
        return detect_format(Path(f"x{ext}"))
    except ValueError:
        raise click.UsageError(f"不支持的目标格式：{ext}")


def _convert_single(src: Path, dst: Path, fmt, verbose, dry_run):
    kind, driver = _resolve_driver(dst, fmt)
    if dry_run:
        click.echo(f"[dry-run] {src.name} → {dst.name}  ({driver})")
        return
    if verbose:
        click.echo(f"转换：{src} → {dst}  [{driver}]")
    try:
        if kind == "vector":
            convert_vector(src, dst, driver)
        else:
            convert_raster(src, dst, driver)
        click.echo(f"✓ {src.name} → {dst.name}")
    except Exception as e:
        click.echo(f"✗ 转换失败：{e}")
        sys.exit(1)


def _convert_batch(src_dir: Path, dst_dir: Path, fmt, verbose, dry_run):
    dst_dir.mkdir(parents=True, exist_ok=True)
    files = collect_input_files(src_dir, ALL_EXTENSIONS)

    if not files:
        click.echo(f"⚠ 未找到可处理的文件，已跳过")
        return

    errors: list[tuple[str, str]] = []
    success = 0

    for f in track(files, description="处理中...") if not verbose else files:
        # 确定输出扩展名
        if fmt:
            ext = f".{fmt.lower()}"
        else:
            ext = f.suffix.lower()
        dst_file = dst_dir / (f.stem + ext)

        if dry_run:
            click.echo(f"[dry-run] {f.name} → {dst_file.name}")
            continue

        try:
            kind, driver = detect_format(dst_file)
            if kind == "vector":
                convert_vector(f, dst_file, driver)
            else:
                convert_raster(f, dst_file, driver)
            success += 1
            if verbose:
                click.echo(f"✓ {f.name} → {dst_file.name}")
        except Exception as e:
            errors.append((f.name, str(e)))
            if verbose:
                click.echo(f"✗ {f.name} — {e}")

    click.echo(f"\n完成：{success} 成功 / {len(errors)} 失败")
    report_errors(errors, dst_dir / "gistools-errors.log" if errors else None)

    if errors:
        sys.exit(1)
```

- [ ] **Step 4: 注册命令到 cli/main.py**

```python
import click
from cli.convert import convert

@click.group()
def cli():
    """GISTools — GIS 操作命令行工具包"""
    pass

cli.add_command(convert)
```

- [ ] **Step 5: 运行确认测试通过**

```bash
pytest tests/test_convert_cmd.py -v
```

期望：全部 PASS

- [ ] **Step 6: 手动冒烟测试**

```bash
gistools convert --help
```

- [ ] **Step 7: Commit**

```bash
git add cli/convert.py cli/main.py tests/test_convert_cmd.py
git commit -m "feat: gistools convert 命令（单文件+批量）"
```

---

## Task 4: 坐标系别名库（core/crs.py）

**Files:**
- Create: `core/crs.py`
- Create: `tests/test_crs.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_crs.py`：

```python
import pytest
from core.crs import resolve_crs

def test_resolve_epsg_string():
    crs = resolve_crs("EPSG:4326")
    assert crs.to_epsg() == 4326

def test_resolve_epsg_number_string():
    crs = resolve_crs("4326")
    assert crs.to_epsg() == 4326

def test_resolve_wgs84_alias():
    crs = resolve_crs("WGS84")
    assert crs.to_epsg() == 4326

def test_resolve_cgcs2000_english():
    crs = resolve_crs("CGCS2000")
    assert crs.to_epsg() == 4490

def test_resolve_cgcs2000_chinese():
    crs = resolve_crs("国家2000")
    assert crs.to_epsg() == 4490

def test_resolve_beijing54():
    crs = resolve_crs("北京54")
    assert crs.to_epsg() == 4214

def test_resolve_xian80():
    crs = resolve_crs("西安80")
    assert crs.to_epsg() == 4610

def test_resolve_unknown():
    with pytest.raises(ValueError, match="无法识别"):
        resolve_crs("火星坐标系XYZ")
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_crs.py -v
```

期望：`ImportError`

- [ ] **Step 3: 实现 core/crs.py**

```python
from pyproj import CRS

CRS_ALIASES: dict[str, str] = {
    "WGS84": "EPSG:4326",
    "CGCS2000": "EPSG:4490",
    "国家2000": "EPSG:4490",
    "北京54": "EPSG:4214",
    "西安80": "EPSG:4610",
    "GCJ02": "EPSG:4326",  # GCJ-02 无标准 EPSG，坐标偏移需额外处理，此处先映射 WGS84
}


def resolve_crs(name: str) -> CRS:
    """
    将用户输入的坐标系名称（EPSG 编码/英文别名/中文别名）解析为 pyproj.CRS。
    无法识别时抛 ValueError。
    """
    key = name.strip()
    mapped = CRS_ALIASES.get(key, key)
    # 纯数字视为 EPSG 编码
    if mapped.isdigit():
        mapped = f"EPSG:{mapped}"
    try:
        return CRS.from_user_input(mapped)
    except Exception:
        raise ValueError(
            f"无法识别的坐标系：{name}\n"
            f"请使用 EPSG 编码（如 EPSG:4326）或别名（如 WGS84、CGCS2000、国家2000）"
        )
```

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/test_crs.py -v
```

期望：全部 PASS

- [ ] **Step 5: Commit**

```bash
git add core/crs.py tests/test_crs.py
git commit -m "feat: 坐标系别名库（中英文 + EPSG 编码）"
```

---

## Task 5: gistools reproject 命令

**Files:**
- Create: `cli/reproject.py`
- Modify: `cli/main.py`
- Create: `tests/test_reproject_cmd.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_reproject_cmd.py`：

```python
import pytest
from click.testing import CliRunner
from cli.main import cli
from pathlib import Path
import geopandas as gpd

@pytest.fixture
def runner():
    return CliRunner()

def test_reproject_wgs84_to_cgcs2000(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.geojson"),
        "--to", "CGCS2000",
    ])
    assert result.exit_code == 0
    gdf = gpd.read_file(tmp_path / "out.geojson")
    assert gdf.crs.to_epsg() == 4490

def test_reproject_chinese_alias(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.geojson"),
        "--to", "国家2000",
    ])
    assert result.exit_code == 0

def test_reproject_epsg_code(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.geojson"),
        "--to", "EPSG:4490",
    ])
    assert result.exit_code == 0

def test_reproject_no_crs_in_file(runner, tmp_path):
    """文件无坐标系 + 未传 --from → 报错"""
    # 创建无 CRS 的 GeoJSON
    import geopandas as gpd
    from shapely.geometry import Point
    gdf = gpd.GeoDataFrame(geometry=[Point(114, 22)])
    # 不设置 crs，直接写出
    gdf.to_file(tmp_path / "nocrs.geojson", driver="GeoJSON")
    result = runner.invoke(cli, [
        "reproject",
        str(tmp_path / "nocrs.geojson"),
        str(tmp_path / "out.geojson"),
        "--to", "CGCS2000",
    ])
    assert result.exit_code == 1
    assert "--from" in result.output

def test_reproject_with_explicit_from(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.geojson"),
        "--to", "CGCS2000",
        "--from", "WGS84",
    ])
    assert result.exit_code == 0

def test_reproject_unknown_crs(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(sample_dir / "points.geojson"),
        str(tmp_path / "out.geojson"),
        "--to", "火星坐标系XYZ",
    ])
    assert result.exit_code == 1
    assert "无法识别" in result.output

def test_reproject_batch(runner, sample_dir, tmp_path):
    result = runner.invoke(cli, [
        "reproject",
        str(sample_dir),
        str(tmp_path),
        "--to", "CGCS2000",
        "--from", "WGS84",
    ])
    assert result.exit_code in (0, 1)
    assert "成功" in result.output
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_reproject_cmd.py -v
```

期望：`No such command 'reproject'`

- [ ] **Step 3: 实现 cli/reproject.py**

```python
import sys
from pathlib import Path
import click
import geopandas as gpd
from rich.progress import track
from core.crs import resolve_crs
from core.formats import VECTOR_DRIVERS
from core.batch import collect_input_files, report_errors


def _reproject_file(src: Path, dst: Path, to_crs, from_crs_name: str | None, verbose: bool):
    """单文件转投影。from_crs_name 为 None 时从文件自动读取。"""
    gdf = gpd.read_file(str(src))

    if from_crs_name:
        gdf = gdf.set_crs(resolve_crs(from_crs_name), allow_override=True)
    elif gdf.crs is None:
        raise RuntimeError(
            f"文件无坐标系信息（缺少 .prj 或 crs 字段）\n"
            f"  请使用 --from 参数手动指定，例如：--from EPSG:4326 或 --from WGS84"
        )

    result = gdf.to_crs(to_crs)
    dst.parent.mkdir(parents=True, exist_ok=True)

    ext = dst.suffix.lower()
    driver = VECTOR_DRIVERS.get(ext, "GeoJSON")
    result.to_file(str(dst), driver=driver)

    if verbose:
        click.echo(f"✓ {src.name} → {dst.name}  [{gdf.crs} → {to_crs}]")


@click.command()
@click.argument("input_path", metavar="<input>", type=click.Path(exists=False))
@click.argument("output_path", metavar="<output>")
@click.option("--to", "to_crs_name", required=True, help="目标坐标系（EPSG 编码/别名/中文名）")
@click.option("--from", "from_crs_name", default=None, help="源坐标系（可选，未指定时从文件读取）")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--dry-run", is_flag=True)
def reproject(input_path, output_path, to_crs_name, from_crs_name, verbose, dry_run):
    """坐标系转换。<input> 和 <output> 可以是文件或文件夹。"""
    src = Path(input_path)
    dst = Path(output_path)

    if not src.exists():
        click.echo(f"✗ 错误：输入路径不存在\n  路径：{src}")
        sys.exit(1)

    if src.is_file() and dst.is_dir():
        raise click.UsageError("输入是文件，输出应为文件路径")
    if src.is_dir() and dst.exists() and dst.is_file():
        raise click.UsageError("输入是文件夹，输出应为文件夹路径")

    try:
        to_crs = resolve_crs(to_crs_name)
    except ValueError as e:
        click.echo(f"✗ {e}")
        sys.exit(1)

    if src.is_file():
        if dry_run:
            click.echo(f"[dry-run] {src.name} → {dst.name}  [→ {to_crs_name}]")
            return
        try:
            _reproject_file(src, dst, to_crs, from_crs_name, verbose)
            if not verbose:
                click.echo(f"✓ {src.name} → {dst.name}")
        except Exception as e:
            click.echo(f"✗ {e}")
            sys.exit(1)
    else:
        dst.mkdir(parents=True, exist_ok=True)
        files = collect_input_files(src, set(VECTOR_DRIVERS.keys()))
        if not files:
            click.echo("⚠ 未找到可处理的矢量文件，已跳过")
            return

        errors: list[tuple[str, str]] = []
        success = 0

        for f in track(files, description="转投影中...") if not verbose else files:
            dst_file = dst / f.name
            if dry_run:
                click.echo(f"[dry-run] {f.name} → {dst_file.name}")
                continue
            try:
                _reproject_file(f, dst_file, to_crs, from_crs_name, verbose)
                success += 1
            except Exception as e:
                errors.append((f.name, str(e)))

        click.echo(f"\n完成：{success} 成功 / {len(errors)} 失败")
        report_errors(errors, dst / "gistools-errors.log" if errors else None)
        if errors:
            sys.exit(1)
```

- [ ] **Step 4: 注册到 cli/main.py**

```python
import click
from cli.convert import convert
from cli.reproject import reproject

@click.group()
def cli():
    """GISTools — GIS 操作命令行工具包"""
    pass

cli.add_command(convert)
cli.add_command(reproject)
```

- [ ] **Step 5: 运行确认测试通过**

```bash
pytest tests/test_reproject_cmd.py -v
```

期望：全部 PASS

- [ ] **Step 6: Commit**

```bash
git add cli/reproject.py cli/main.py tests/test_reproject_cmd.py
git commit -m "feat: gistools reproject 命令（含中文别名 + 无CRS报错）"
```

---

## Task 6: gistools buffer 命令

**Files:**
- Create: `core/spatial.py`
- Create: `cli/buffer.py`
- Modify: `cli/main.py`
- Create: `tests/test_spatial.py`
- Create: `tests/test_buffer_cmd.py`

- [ ] **Step 1: 写 spatial.py 失败测试**

创建 `tests/test_spatial.py`：

```python
import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString
from pathlib import Path
from core.spatial import buffer_file

@pytest.fixture
def point_file(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    )
    p = tmp_path / "points.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return p

@pytest.fixture
def line_file(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[LineString([(114.0, 22.5), (114.1, 22.6)])],
        crs="EPSG:4326",
    )
    p = tmp_path / "line.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return p

def test_buffer_points_meters(point_file, tmp_path):
    dst = tmp_path / "out.geojson"
    buffer_file(point_file, dst, distance=500, unit="meters", dissolve=False)
    result = gpd.read_file(dst)
    assert len(result) == 2
    assert result.geometry.geom_type.iloc[0] == "Polygon"

def test_buffer_line_km(line_file, tmp_path):
    dst = tmp_path / "out.geojson"
    buffer_file(line_file, dst, distance=1, unit="km", dissolve=False)
    result = gpd.read_file(dst)
    assert len(result) == 1

def test_buffer_dissolve(point_file, tmp_path):
    dst = tmp_path / "out.geojson"
    buffer_file(point_file, dst, distance=100000, unit="meters", dissolve=True)
    result = gpd.read_file(dst)
    assert len(result) == 1  # 合并为单个要素

def test_buffer_empty_input(tmp_path):
    """0 个要素 → 输出空文件，不报错"""
    gdf = gpd.GeoDataFrame({"id": []}, geometry=[], crs="EPSG:4326")
    src = tmp_path / "empty.geojson"
    gdf.to_file(src, driver="GeoJSON")
    dst = tmp_path / "out.geojson"
    buffer_file(src, dst, distance=500, unit="meters", dissolve=False)
    assert dst.exists()
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_spatial.py -v
```

期望：`ImportError`

- [ ] **Step 3: 实现 core/spatial.py**

```python
from pathlib import Path
import geopandas as gpd
import click


def buffer_file(src: Path, dst: Path, distance: float, unit: str, dissolve: bool) -> None:
    """
    对矢量文件做缓冲区分析。
    unit: 'meters' | 'km' | 'degrees'
    dissolve: 是否合并所有缓冲要素为单一几何
    """
    gdf = gpd.read_file(str(src))

    if len(gdf) == 0:
        click.echo(f"⚠ 输入数据无要素，输出为空文件：{dst.name}")
        gdf.to_file(str(dst), driver="GeoJSON")
        return

    if unit == "km":
        distance_m = distance * 1000
        unit = "meters"
    else:
        distance_m = distance

    if unit == "meters":
        crs_orig = gdf.crs
        gdf_proj = gdf.to_crs(gdf.estimate_utm_crs())
        buffered = gdf_proj.copy()
        buffered.geometry = gdf_proj.geometry.buffer(distance_m)
        buffered = buffered.to_crs(crs_orig)
    else:  # degrees
        buffered = gdf.copy()
        buffered.geometry = gdf.geometry.buffer(distance_m)

    if dissolve:
        buffered = buffered.dissolve()

    dst.parent.mkdir(parents=True, exist_ok=True)
    buffered.to_file(str(dst), driver="GeoJSON")
```

- [ ] **Step 4: 运行确认 spatial 测试通过**

```bash
pytest tests/test_spatial.py -v
```

期望：全部 PASS

- [ ] **Step 5: 写 buffer 命令测试**

创建 `tests/test_buffer_cmd.py`：

```python
import pytest
from click.testing import CliRunner
from cli.main import cli
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def point_geojson(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[Point(114.0, 22.5)],
        crs="EPSG:4326",
    )
    p = tmp_path / "point.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return p

def test_buffer_basic(runner, point_geojson, tmp_path):
    result = runner.invoke(cli, [
        "buffer",
        str(point_geojson),
        str(tmp_path / "out.geojson"),
        "--distance", "500",
    ])
    assert result.exit_code == 0
    assert (tmp_path / "out.geojson").exists()

def test_buffer_km_unit(runner, point_geojson, tmp_path):
    result = runner.invoke(cli, [
        "buffer", str(point_geojson), str(tmp_path / "out.geojson"),
        "--distance", "1", "--unit", "km",
    ])
    assert result.exit_code == 0

def test_buffer_dissolve(runner, tmp_path):
    gdf = gpd.GeoDataFrame(
        geometry=[Point(114.0, 22.5), Point(114.001, 22.501)],
        crs="EPSG:4326",
    )
    src = tmp_path / "pts.geojson"
    gdf.to_file(src, driver="GeoJSON")
    result = runner.invoke(cli, [
        "buffer", str(src), str(tmp_path / "out.geojson"),
        "--distance", "500", "--dissolve",
    ])
    assert result.exit_code == 0

def test_buffer_rejects_raster(runner, tmp_path):
    """传入栅格文件应立即报错"""
    fake_tif = tmp_path / "dem.tif"
    fake_tif.write_bytes(b"not a real tiff")
    result = runner.invoke(cli, [
        "buffer", str(fake_tif), str(tmp_path / "out.geojson"),
        "--distance", "500",
    ])
    assert result.exit_code == 1
    assert "矢量" in result.output

def test_buffer_missing_distance(runner, point_geojson, tmp_path):
    result = runner.invoke(cli, [
        "buffer", str(point_geojson), str(tmp_path / "out.geojson"),
    ])
    assert result.exit_code == 2  # click UsageError

def test_buffer_batch(runner, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    gdf = gpd.GeoDataFrame(geometry=[Point(114.0, 22.5)], crs="EPSG:4326")
    gdf.to_file(src_dir / "a.geojson", driver="GeoJSON")
    result = runner.invoke(cli, [
        "buffer", str(src_dir), str(dst_dir), "--distance", "500",
    ])
    assert result.exit_code in (0, 1)
    assert "成功" in result.output
```

- [ ] **Step 6: 运行确认失败**

```bash
pytest tests/test_buffer_cmd.py -v
```

期望：`No such command 'buffer'`

- [ ] **Step 7: 实现 cli/buffer.py**

```python
import sys
from pathlib import Path
import click
from rich.progress import track
from core.formats import detect_format, VECTOR_DRIVERS, RASTER_DRIVERS
from core.spatial import buffer_file
from core.batch import collect_input_files, report_errors


@click.command()
@click.argument("input_path", metavar="<input>", type=click.Path(exists=False))
@click.argument("output_path", metavar="<output>")
@click.option("--distance", required=True, type=float, help="缓冲距离（必填）")
@click.option("--unit", default="meters", type=click.Choice(["meters", "km", "degrees"]), help="距离单位（默认 meters）")
@click.option("--dissolve", is_flag=True, help="合并所有缓冲区为单个要素")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--dry-run", is_flag=True)
def buffer(input_path, output_path, distance, unit, dissolve, verbose, dry_run):
    """缓冲区分析（仅限矢量数据）。<input> 和 <output> 可以是文件或文件夹。"""
    src = Path(input_path)
    dst = Path(output_path)

    if not src.exists():
        click.echo(f"✗ 错误：输入路径不存在\n  路径：{src}")
        sys.exit(1)

    if src.is_file() and dst.is_dir():
        raise click.UsageError("输入是文件，输出应为文件路径")
    if src.is_dir() and dst.exists() and dst.is_file():
        raise click.UsageError("输入是文件夹，输出应为文件夹路径")

    if src.is_file():
        _buffer_single(src, dst, distance, unit, dissolve, verbose, dry_run)
    else:
        _buffer_batch(src, dst, distance, unit, dissolve, verbose, dry_run)


def _check_not_raster(path: Path):
    ext = path.suffix.lower()
    if ext in RASTER_DRIVERS:
        click.echo(
            f"✗ gistools buffer 仅支持矢量数据（点/线/面）\n"
            f"  文件：{path.name} 是栅格格式，无法处理"
        )
        sys.exit(1)


def _buffer_single(src, dst, distance, unit, dissolve, verbose, dry_run):
    _check_not_raster(src)
    if dry_run:
        click.echo(f"[dry-run] {src.name} → {dst.name}  [buffer {distance} {unit}]")
        return
    try:
        buffer_file(src, dst, distance, unit, dissolve)
        click.echo(f"✓ {src.name} → {dst.name}")
    except Exception as e:
        click.echo(f"✗ 缓冲区计算失败：{e}")
        sys.exit(1)


def _buffer_batch(src_dir, dst_dir, distance, unit, dissolve, verbose, dry_run):
    dst_dir.mkdir(parents=True, exist_ok=True)
    files = collect_input_files(src_dir, set(VECTOR_DRIVERS.keys()))
    if not files:
        click.echo("⚠ 未找到可处理的矢量文件，已跳过")
        return

    errors: list[tuple[str, str]] = []
    success = 0

    for f in track(files, description="Buffer 中...") if not verbose else files:
        dst_file = dst_dir / f.name
        if dry_run:
            click.echo(f"[dry-run] {f.name} → {dst_file.name}")
            continue
        try:
            buffer_file(f, dst_file, distance, unit, dissolve)
            success += 1
            if verbose:
                click.echo(f"✓ {f.name}")
        except Exception as e:
            errors.append((f.name, str(e)))
            if verbose:
                click.echo(f"✗ {f.name} — {e}")

    click.echo(f"\n完成：{success} 成功 / {len(errors)} 失败")
    report_errors(errors, dst_dir / "gistools-errors.log" if errors else None)
    if errors:
        sys.exit(1)
```

- [ ] **Step 8: 注册到 cli/main.py**

```python
import click
from cli.convert import convert
from cli.reproject import reproject
from cli.buffer import buffer

@click.group()
def cli():
    """GISTools — GIS 操作命令行工具包"""
    pass

cli.add_command(convert)
cli.add_command(reproject)
cli.add_command(buffer)
```

- [ ] **Step 9: 运行全部测试**

```bash
pytest tests/ -v
```

期望：全部 PASS

- [ ] **Step 10: Commit**

```bash
git add core/spatial.py cli/buffer.py cli/main.py tests/test_spatial.py tests/test_buffer_cmd.py
git commit -m "feat: gistools buffer 命令（含栅格拒绝 + dissolve）"
```

---

## Task 7: 端到端冒烟测试

**Files:** 无新增文件

- [ ] **Step 1: 用真实 GIS 文件跑三个命令**

```bash
conda activate pytorch
cd D:\zjn\code\gistools

# 如果手边有 SHP 文件，替换路径；否则用 pytest 生成的临时文件
gistools convert --help
gistools reproject --help
gistools buffer --help
```

- [ ] **Step 2: 运行完整测试套件并确认通过**

```bash
pytest tests/ -v --tb=short
```

期望：全部测试 PASS，无 ERROR

- [ ] **Step 3: 验证退出码**

```bash
# 应退出 0
gistools convert tests/sample_data/points.geojson /tmp/out.shp; echo "exit: $?"

# 应退出 1（文件不存在）
gistools convert /tmp/notexist.shp /tmp/out.geojson; echo "exit: $?"
```

- [ ] **Step 4: 最终 Commit**

```bash
git add -A
git commit -m "test: 端到端冒烟测试通过，原型 v0.1 完成"
```

---

## 自检：Spec 覆盖确认

| 设计要求 | 对应 Task |
|----------|-----------|
| gistools convert 单文件/批量 | Task 3 |
| gistools reproject 单文件/批量 | Task 5 |
| gistools buffer 单文件/批量 | Task 6 |
| 同名文件自动覆盖 | Task 3 Step 3（convert_vector 中 DeleteDataSource） |
| 无 CRS 时报错提示 --from | Task 5 Step 3（_reproject_file） |
| 批量错误 ≤10 终端 / >10 写 log | Task 2 Step 3（report_errors） |
| 批量遇错继续不中断 | Task 3/5/6 batch 函数 |
| 空文件夹打印警告退出 0 | Task 3 Step 3（_convert_batch） |
| buffer 拒绝栅格输入 | Task 6 Step 7（_check_not_raster） |
| --dry-run 验证但不写文件 | Task 3/5/6 各命令 dry_run 分支 |
| --verbose 显示每文件步骤 | Task 3/5/6 verbose 分支 |
| 退出码 0/1/2 规范 | 贯穿所有命令 |
| input/output 类型一致性检查 | Task 3/5/6 各命令开头 |
| Python 3.10+ | Task 0 pyproject.toml |
| conda pytorch 环境开发 | Task 0 Step 1 |
