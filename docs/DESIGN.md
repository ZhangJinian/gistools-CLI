# GISTools CLI 设计文档

> 本文档是项目的唯一设计文档，每次重要变更后更新此文件。
> 版本通过 Git Tag 管理。

---

## 项目概述

**项目名称：** GISTools CLI
**定位：** 面向 GIS 从业者和开发者的命令行工具包，将常用 GIS 操作封装为标准 CLI 命令
**安装方式：** `npm install -g gistools`（打包后）/ `pip install -e .`（开发）
**运行环境：** Python 3.9+ / GDAL 2.4+ / conda PyTorch 环境
**设计语言：** 参考 ArcGIS Pro Conversion 工具箱

---

## 命令总览

| 命令 | 功能 | 实现 |
|------|------|------|
| `gistools convert` | 格式转换（所有子命令的入口） | Click group |
| `gistools reproject` | 坐标系转换 | pyproj |
| `gistools buffer` | 缓冲区分析（仅矢量） | Shapely |
| `gistools geojson-validate` | GeoJSON 文件验证 | json/Fiona |

### convert 子命令总览

| 子命令 | 功能 | GDAL 函数 |
|--------|------|-----------|
| `gistools convert format` | 同格式互转（矢量↔矢量 / 栅格↔栅格） | ogr.CopyDataSource / gdal.CreateCopy |
| `gistools convert raster2polygon` | 栅格转面（TIFF → SHP/GeoJSON） | gdal.Polygonize |
| `gistools convert raster2point` | 栅格转点（像元中心） | gdal.Open 遍历 |
| `gistools convert feature2raster` | 矢量转栅格（SHP/GeoJSON → TIFF） | gdal.Rasterize |

---

## 一、convert — 格式转换工具箱

`convert` 是一个 Click Group 命令，作为转换工具箱的统一入口。

### 1.1 convert format — 同格式互转

```bash
gistools convert format <input> <output> [--format <格式>]
```

**支持格式：**

| 类型 | 扩展名 | GDAL Driver |
|------|--------|-------------|
| 矢量 | .shp .geojson .kml .gml .gpkg .csv | ESRI Shapefile / GeoJSON / KML / GML / GPKG / CSV |
| 栅格 | .tif .tiff .img .hdf .nc | GTiff / HFA / HDF4 / netCDF |

**转换限制：**
- 矢量 ↔ 矢量：✓ 支持
- 栅格 ↔ 栅格：✓ 支持
- 矢量 → 栅格：✗ 不支持（请用 `feature2raster`）
- 栅格 → 矢量：✗ 不支持（请用 `raster2polygon` 或 `raster2point`）

**参数：**
- `<input>` — 输入文件或文件夹
- `<output>` — 输出文件或文件夹
- `--format` — 目标格式；可从输出扩展名推断，显式指定时优先级更高

**批量模式：** 同一文件夹内所有指定格式文件全部转换，遇错继续，完成后汇报失败列表。

---

### 1.2 convert raster2polygon — 栅格转面

```bash
gistools convert raster2polygon <input> <output> [--field <字段名>] [--simplify <容差>] [--multi]
```

**功能：** 将栅格的有效像元区域转为矢量面要素。

**参数：**
- `--field <name>` — 栅格值写入输出属性表的字段名（默认 `DN`）
- `--simplify <tol>` — 简化几何的容差（GDAL 单位，不指定则不简化）
- `--multi` — 将所有多边形合并为单一 MultiPolygon 输出

**GDAL 实现：** `gdal.Polygonize(band, maskBand, dst_layer, field_index)`

**使用示例：**
```bash
gistools convert raster2polygon dem.tif zones.shp
gistools convert raster2polygon dem.tif zones.shp --field GRIDCODE --simplify 0.5
gistools convert raster2polygon dem.tif zones.geojson --multi
```

---

### 1.3 convert raster2point — 栅格转点

```bash
gistools convert raster2point <input> <output> [--field <字段名>]
```

**功能：** 将栅格每个有效像元的中心转为点要素。

**参数：**
- `--field <name>` — 像元值写入的属性字段名（默认 `value`）

**GDAL 实现：** 遍历栅格波段，读每个有效像元的中心坐标 (x, y) 和值，写入点要素。

**使用示例：**
```bash
gistools convert raster2point dem.tif points.shp
gistools convert raster2point dem.tif points.geojson --field ELEVATION
```

---

### 1.4 convert feature2raster — 矢量转栅格

```bash
gistools convert feature2raster <input> <output> --cellsize <数值> [--field <字段名>] [--extent <xmin ymin xmax ymax>]
```

**功能：** 将矢量要素"烧录"到栅格格网中。

**参数：**
- `--cellsize <数值>` — **必填**。像元大小（GDAL 单位，与输入坐标系单位一致）
- `--field <name>` — 按某字段值填入栅格；未指定时填 1（二值栅格）
- `--extent <xmin ymin xmax ymax>` — 手动指定输出范围；未指定时自动从矢量外包范围计算

**GDAL 实现：** `gdal.Rasterize(dst_ds, [1], src_layer)` + 设置 GeoTransform

**使用示例：**
```bash
gistools convert feature2raster zone.shp zone.tif --cellsize 30
gistools convert feature2raster zone.shp zone.tif --cellsize 0.001 --field POPULATION
gistools convert feature2raster zone.shp zone.tif --cellsize 30 --extent "100 20 200 50"
```

---

## 二、reproject — 坐标系转换

```bash
gistools reproject <input> <output> --to <目标坐标系> [--from <源坐标系>]
```

**坐标系别名：**

| 别名 | EPSG |
|------|------|
| WGS84 | 4326 |
| CGCS2000 / 国家2000 | 4490 |
| 北京54 | 4214 |
| 西安80 | 4610 |

**无坐标系处理：** 若文件无 `.prj` 且未传 `--from`，报错提示用户手动指定。

---

## 三、buffer — 缓冲区分析

```bash
gistools buffer <input> <output> --distance <数值> [--unit <meters|km|degrees>] [--dissolve]
```

**说明：** 仅支持矢量数据（点/线/面）。

- `--unit meters`（默认）：自动转换到 UTM 投影计算后再转回
- `--unit km`：同 meters，换算后处理
- `--unit degrees`：直接 buffer（精度低，不推荐）
- `--dissolve`：合并所有缓冲区为单一要素

**空要素处理：** 输入要素数为 0 时，输出空文件，退出码 0。

---

## 四、geojson-validate — GeoJSON 验证

```bash
gistools geojson-validate <input>
```

**功能：** 验证 GeoJSON 合法性，打印结构信息（要素数、CRS、属性字段），不写输出文件。

**退出码：** 0 = 合法，1 = 非法。

---

## 五、通用规范

### 5.1 输入/输出类型一致性

| input | output | 行为 |
|-------|--------|------|
| 文件 | 文件 | 单文件操作 |
| 文件夹 | 文件夹 | 批量操作 |
| 文件 | 文件夹 | ✗ 报错 exit 2 |
| 文件夹 | 文件 | ✗ 报错 exit 2 |

### 5.2 批量错误处理

- 遇错继续处理其余文件，不中断
- 失败 ≤ 10 条：终端直接打印
- 失败 > 10 条：终端打印前 10 条，完整列表写入 `<output>/gistools-errors.log`

### 5.3 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 全部成功（含空文件夹跳过） |
| 1 | 有文件处理失败 |
| 2 | 参数错误 |

### 5.4 通用参数

| 参数 | 说明 |
|------|------|
| `--verbose` / `-v` | 显示每步处理详情 |
| `--dry-run` | 预览操作，不实际执行 |
| `--help` / `-h` | 显示帮助 |

---

## 六、技术栈

| 用途 | 库 |
|------|-----|
| CLI 框架 | Click 8.x |
| 矢量 I/O | GDAL/OGR（osgeo） |
| 栅格 I/O | GDAL（osgeo） |
| 坐标系 | pyproj 3.x |
| 空间操作 | Shapely 2.x + GeoPandas 1.x |
| 进度条 | rich |
| 测试 | pytest |

---

## 七、项目结构

```
gistools/
├── cli/
│   ├── main.py              # Click group，注册所有命令
│   ├── convert.py          # convert 命令组（含 format/raster2polygon/raster2point/feature2raster 子命令）
│   ├── reproject.py        # reproject 命令
│   ├── buffer.py           # buffer 命令
│   └── geojson_validate.py # geojson-validate 命令
├── core/
│   ├── formats.py          # 格式检测、同格式转换
│   ├── crs.py             # 坐标系别名
│   ├── spatial.py         # buffer 核心逻辑
│   ├── batch.py           # 批量处理基础设施
│   ├── rasterize.py       # Polygonize/Rasterize 核心实现
│   └── geojson_utils.py   # GeoJSON 验证
├── tests/                  # pytest 测试
├── docs/
│   └── DESIGN.md          # 本文档（唯一设计文档）
├── pyproject.toml
└── package.json
```

---

## 八、版本历史

通过 Git Tag 管理，每次发布打 tag。

| Tag | 版本 | 日期 | 变更 |
|-----|------|------|------|
| v0.1 | 0.1.0 | 2026-04-15 | 初始版本：convert(format)、reproject、buffer |
| v0.2 | 0.2.0 | 2026-04-17 | 新增：convert raster2polygon、raster2point、feature2raster；修复：buffer 输出格式 bug、矢量↔栅格非法转换无提示 bug |

---

## 九、分发方案

```
打包后分发（目标）：
npm install -g gistools
  → postinstall 下载 PyInstaller 打包的 .exe（含 Python + GDAL）

开发阶段：
pip install -e .
  → 直接用源码运行
```

---

## 十、已知限制

- Python 3.9 / GDAL 2.4 环境开发，其他版本未充分测试
- `--unit degrees` 的 buffer 精度低，慎用
- feature2raster 的 `--extent` 参数尚未实现（自动从矢量范围计算）
- GeoJSON Validate 尚未实现（计划中）
