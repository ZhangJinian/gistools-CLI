# GISTools CLI — 原型设计文档

**日期：** 2026-04-15
**阶段：** 原型（Prototype v0.1）
**作者：** zjn
**修订：** v1.1（根据设计评审补充关键细节）

---

## 1. 项目概述

### 定位

GISTools 是一个面向 GIS 从业者和开发者的命令行工具包，将常用 GIS 操作封装为标准 CLI 命令，支持在 Windows CMD / PowerShell 中直接调用。

用户通过 `npm install -g gistools` 安装，无需手动配置 Python 或 GDAL 环境。

### 两层架构

```
GISTools CLI（本期原型）
└── 独立可用，封装 GIS 操作为标准命令

GeoClaw Agent（后续阶段）
└── AI 层，理解自然语言 → 编排调用 GISTools 命令 → 返回结果
```

---

## 2. 运行环境要求

### 开发环境（原型阶段）

- **Python：** 3.10+（与 Anaconda pytorch 环境一致）
- **GDAL：** 使用本机 Anaconda pytorch 环境中已有的 GDAL，无需另装
- **激活方式：** `conda activate pytorch`，然后 `python -m gistools`

### 用户环境（分发阶段）

| 分发方式 | 用户要求 |
|----------|----------|
| PyInstaller 打包（优先尝试） | 无需 Python，`npm install -g gistools` 即可 |
| 无法打包时的降级方案 | 需要用户有 Python 3.10+ 环境，首次运行提示安装依赖 |

> **打包策略：** 先尝试 PyInstaller + GDAL DLL 捆绑。若打包产物无法正常调用 GDAL（常见于 Windows），降级为要求用户指定 Python 环境路径，通过 `gistools config --python-path C:\anaconda\envs\pytorch\python.exe` 配置。

---

## 3. 本期范围（原型 v0.1）

实现三个核心命令，验证技术可行性：

| 命令 | 功能 |
|------|------|
| `gistools convert` | 矢量/栅格格式互转 |
| `gistools reproject` | 坐标系转换 |
| `gistools buffer` | 缓冲区分析（仅限矢量数据） |

---

## 4. 命令接口规范

### 4.1 格式转换 — `gistools convert`

```bash
gistools convert <input> <output> [--format <格式>]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `<input>` | 输入文件路径或文件夹路径 |
| `<output>` | 输出文件路径或文件夹路径 |
| `--format` | 目标格式（见下表）；可从输出路径扩展名自动推断，显式指定时优先级更高 |

**`--format` 与输出扩展名的优先级：**
- 显式传入 `--format` → 以 `--format` 为准
- 未传 `--format`，输出路径有扩展名 → 从扩展名推断
- 两者都缺 → 报错提示用户指定

**支持格式：**

| 类型 | 格式 |
|------|------|
| 矢量 | `shp` / `geojson` / `kml` / `gml` / `gpkg` / `csv` |
| 栅格 | `tiff` / `geotiff` / `img` / `hdf` / `nc`（NetCDF） |

**批量模式（input/output 均为文件夹）：**
- 输出文件名 = 输入文件名（去掉原扩展名）+ 目标格式扩展名
  - 示例：`data/roads.shp` → `out/roads.geojson`
- **同名文件已存在：自动覆盖，不提示**
- 输入文件夹为空或无可处理文件：打印 `⚠ 未找到可处理的文件，已跳过` 并以退出码 `0` 退出

**示例：**
```bash
gistools convert ./data/roads.shp ./out/roads.geojson
gistools convert ./data/ ./out/ --format geojson
gistools convert ./dem.tif ./dem.img
```

---

### 4.2 坐标系转换 — `gistools reproject`

```bash
gistools reproject <input> <output> --to <目标坐标系> [--from <源坐标系>]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `<input>` | 输入文件路径或文件夹 |
| `<output>` | 输出文件路径或文件夹 |
| `--to` | 目标坐标系（EPSG 编码 / 英文别名 / 中文别名） |
| `--from` | 源坐标系（可选；未指定时从文件元数据自动读取） |

**坐标系识别规则（按优先级）：**
1. 用户显式传入 `--from`
2. 从文件元数据读取（SHP 的 `.prj`、GeoJSON 的 `crs` 字段等）
3. 若元数据中无坐标系信息且用户未指定 → **报错**，提示用户手动指定：
   ```
   ✗ 无法识别源坐标系
     文件：./data.shp（缺少 .prj 文件）
     请使用 --from 参数手动指定，例如：
       --from EPSG:4326
       --from WGS84
   ```

**坐标系别名映射（`core/crs.py` 维护）：**

| 中文名 / 英文别名 | 对应 EPSG |
|------------------|-----------|
| `WGS84` | EPSG:4326 |
| `CGCS2000` / `国家2000` | EPSG:4490 |
| `北京54` | EPSG:4214 |
| `西安80` | EPSG:4610 |
| `GCJ02` | 无标准 EPSG，需特殊处理 |

> `crs.py` 维护完整别名字典，可持续扩展。输入内容先查别名表，未命中则尝试直接解析为 EPSG 编码，仍失败则报错。

**批量模式：**
- 输出文件命名规则同 4.1（同名自动覆盖）
- 某文件无坐标系信息：记为失败，继续处理其余文件，汇总时报告

**示例：**
```bash
gistools reproject ./data.shp ./out.shp --to EPSG:4490
gistools reproject ./data.shp ./out.shp --to CGCS2000
gistools reproject ./data/ ./out/ --to WGS84 --from 北京54
```

---

### 4.3 缓冲区分析 — `gistools buffer`

```bash
gistools buffer <input> <output> --distance <数值> [--unit <单位>] [--dissolve]
```

> **仅支持矢量数据。** 传入栅格文件时立即报错：
> ```
> ✗ gistools buffer 仅支持矢量数据（点/线/面）
>   文件：./dem.tif 是栅格格式，无法处理
> ```

**参数：**

| 参数 | 说明 |
|------|------|
| `<input>` | 输入矢量文件或文件夹 |
| `<output>` | 输出文件或文件夹 |
| `--distance` | 缓冲距离（必填，正数） |
| `--unit` | 距离单位：`meters`（默认）/ `km` / `degrees` |
| `--dissolve` | 将所有缓冲区合并为单个要素 |

**`--dissolve` 边界情况：**
- 输入要素数为 0 → 输出空文件，打印警告 `⚠ 输入数据无要素，输出为空文件`，退出码 `0`

**批量模式：**
- 输出文件命名规则同 4.1（同名自动覆盖）
- 批量中遇到栅格文件：记为失败，继续处理其余文件

**示例：**
```bash
gistools buffer ./roads.shp ./buffer.shp --distance 500
gistools buffer ./roads.shp ./buffer.shp --distance 1 --unit km --dissolve
gistools buffer ./points/ ./buffers/ --distance 200
```

---

### 4.4 通用参数（所有命令均支持）

| 参数 | 行为 |
|------|------|
| `--verbose` / `-v` | 打印每个文件的处理步骤（读取→转换→写出）及耗时；不传则只显示进度条和最终结果 |
| `--dry-run` | 验证输入文件是否存在、格式/坐标系是否可识别，打印将要执行的操作列表，**不实际读写文件** |
| `--help` / `-h` | 显示帮助信息和示例 |

**`--dry-run` 示例输出：**
```
[dry-run] 将执行以下操作（共 3 个文件）：
  roads.shp     → roads.geojson   ✓ 可处理
  buildings.shp → buildings.geojson ✓ 可处理
  broken.shp    → broken.geojson  ✗ 缺少 .prj，需指定 --from
（未实际执行，移除 --dry-run 后生效）
```

---

### 4.5 输入/输出类型一致性规则

| input 类型 | output 类型 | 行为 |
|-----------|------------|------|
| 文件 | 文件 | 单文件操作 |
| 文件夹 | 文件夹 | 批量操作 |
| 文件 | 文件夹 | 报错：输入是文件，输出应为文件路径 |
| 文件夹 | 文件 | 报错：输入是文件夹，输出应为文件夹路径 |

---

## 5. 错误处理规范

### 单文件操作出错

直接打印错误，退出码 `1`：

```
✗ 错误：输入文件不存在
  路径：./notexist.shp

✗ 转换失败：无法读取文件
  文件：./broken.shp
  原因：SHP 文件缺少对应的 .dbf 属性表
  建议：确认 .shp / .dbf / .prj 三个文件在同一目录下
```

### 批量操作出错

- 遇到失败文件**继续处理**，不中断
- 全部完成后终端汇总：
  - **失败 ≤ 10 条**：终端直接列出
  - **失败 > 10 条**：终端显示前 10 条，完整列表写入 `<output>/gistools-errors.log`

```
完成：47 成功 / 3 失败

失败文件：
  · file_01.shp — 缺少 .prj 投影文件，请用 --from 指定坐标系
  · file_03.shp — 文件已损坏，无法读取
  · file_09.shp — 不支持的格式
```

### 退出码规范

| 退出码 | 含义 |
|--------|------|
| `0` | 全部成功（含空文件夹跳过） |
| `1` | 有文件处理失败（部分或全部） |
| `2` | 参数错误（命令写法有误） |

---

## 6. 技术栈

| 层次 | 库 / 工具 | 用途 |
|------|-----------|------|
| CLI 框架 | Click 8.x | 命令注册、参数解析、彩色输出 |
| 格式转换 | GDAL / OGR（`osgeo`） | 矢量/栅格读写，40+ 格式 |
| 坐标系转换 | pyproj 3.x | EPSG 数据库、坐标变换 |
| 空间操作 | Shapely 2.x + GeoPandas | Buffer 计算、dissolve 合并 |
| 进度显示 | rich | 进度条、彩色终端输出 |

---

## 7. 项目结构

```
gistools/
├── cli/
│   ├── __init__.py
│   ├── main.py          # 入口，注册所有子命令
│   ├── convert.py       # gistools convert 实现
│   ├── reproject.py     # gistools reproject 实现
│   └── buffer.py        # gistools buffer 实现
├── core/
│   ├── __init__.py
│   ├── formats.py       # 格式检测、转换逻辑
│   ├── crs.py           # 坐标系别名字典（中文名/英文别名 → EPSG）
│   └── spatial.py       # 空间操作（buffer、dissolve）
├── tests/
│   ├── sample_data/     # 测试用 SHP / GeoJSON 样本数据
│   ├── test_convert.py
│   ├── test_reproject.py
│   └── test_buffer.py
├── docs/
│   └── 2026-04-15-gistools-design.md
├── pyproject.toml       # 依赖声明（Python 3.10+）
└── package.json         # npm 包壳（分发用）
```

---

## 8. 分发方案

```
开发完成后的分发流程：

1. 尝试 PyInstaller + GDAL DLL 捆绑 → gistools-win-x64.exe
   └── 若打包验证通过（调用 gistools convert 能正常处理文件）→ 走 npm 分发
   └── 若 GDAL DLL 调用失败 → 降级方案：

2. 降级方案：npm 包运行时检测 Python 环境
   └── 首次运行提示：
       "未检测到 Python 环境，请运行：gistools config --python-path <path>"
   └── 用户配置后写入 %APPDATA%/gistools/config.json

3. npm postinstall 脚本下载对应平台二进制，写入 PATH
```

---

## 9. 原型验证目标

| 功能 | 验证项 |
|------|--------|
| 格式转换 | SHP→GeoJSON、GeoJSON→KML、GeoTIFF 转换、批量文件夹、同名覆盖 |
| 坐标系转换 | WGS84↔CGCS2000、EPSG编码、中文别名、无.prj时报错提示 |
| 缓冲区 | 点/线/面要素、meters/km单位、dissolve合并、栅格输入报错 |
| 通用 | --dry-run 验证、批量错误汇总（≤10/＞10两种情况）、退出码正确 |

---

## 10. 开发步骤

1. **环境验证**：`conda activate pytorch`，确认 `from osgeo import ogr` 可正常导入
2. 实现 `gistools convert`（含批量、覆盖、空文件夹处理）
3. 实现 `gistools reproject`（含别名库、无坐标系报错）
4. 实现 `gistools buffer`（含栅格拒绝、dissolve 边界情况）
5. 补充 `--dry-run` 和 `--verbose` 逻辑
6. 端到端测试全部验证目标
7. 评估 PyInstaller 打包可行性
