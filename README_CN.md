# GISTools CLI

面向 GIS 从业者和开发者的命令行工具包，将常用 GIS 操作封装为标准 CLI 命令。

## 安装

**开发环境：**
```bash
pip install -e .
```

**依赖：** Python 3.9+ / GDAL 2.4+

## 快速开始

```bash
# 查看所有命令
gistools --help

# convert 工具箱
gistools convert --help

# raster2polygon — 栅格转面
gistools convert raster2polygon input.tif output.shp --field DN

# raster2point — 栅格转点
gistools convert raster2point input.tif output.shp

# shp2raster — 矢量转栅格
gistools convert shp2raster input.shp output.tif --cellsize 30

# shp2geojson — SHP 转 GeoJSON
gistools convert shp2geojson input.shp output.geojson

# geojson2shp — GeoJSON 转 SHP
gistools convert geojson2shp input.geojson output.shp

# 坐标系转换
gistools reproject input.shp output.shp --to WGS84

# 缓冲区分析
gistools buffer input.shp output.shp --distance 100 --unit meters

# Analysis 工具箱
gistools analysis clip input.shp clip_zone.shp output.shp
gistools analysis intersect a.shp b.shp output.shp
gistools analysis union a.shp b.shp output.shp
gistools analysis dissolve zones.shp dissolved.shp --by region
gistools analysis spatial-join points.shp zones.shp joined.shp --predicate intersects --how left

# Spatial Analyst 工具箱
gistools spatial slope dem.tif slope.tif
gistools spatial aspect dem.tif aspect.tif
gistools spatial hillshade dem.tif hillshade.tif
gistools spatial contour dem.tif contour.shp --interval 10

# Data Management 工具箱
gistools data merge a.shp b.shp output.shp
gistools data split zones.shp out_dir/ --by region
gistools data feature-to-line polygons.shp lines.shp
gistools data feature-to-polygon lines.shp polygons.shp
gistools data add-field input.shp output.shp --name new_field --type REAL --value 0
gistools data delete-field input.shp output.shp --name unused_field
```

## 功能总览

| 命令 | 功能 |
|------|------|
| `gistools convert raster2polygon` | 栅格 → 面要素（gdal.Polygonize） |
| `gistools convert raster2point` | 栅格 → 点要素（像元中心遍历） |
| `gistools convert shp2raster` | 矢量 → 栅格（gdal.Rasterize） |
| `gistools convert shp2geojson` | SHP → GeoJSON |
| `gistools convert geojson2shp` | GeoJSON → SHP |
| `gistools reproject` | 坐标系转换（支持 EPSG/中文别名） |
| `gistools buffer` | 缓冲区分析（支持米/千米/度单位） |
| `gistools analysis clip` | 裁剪 |
| `gistools analysis intersect` | 交集 |
| `gistools analysis union` | 合并 |
| `gistools analysis dissolve` | 融合（按字段） |
| `gistools analysis spatial-join` | 空间连接 |
| `gistools spatial slope` | 坡度分析 |
| `gistools spatial aspect` | 坡向分析 |
| `gistools spatial hillshade` | 山体阴影 |
| `gistools spatial contour` | 等高线生成 |
| `gistools data merge` | 合并多个矢量文件 |
| `gistools data split` | 按字段分割 |
| `gistools data feature-to-line` | 面/线转线 |
| `gistools data feature-to-polygon` | 线转面 |
| `gistools data add-field` | 添加字段 |
| `gistools data delete-field` | 删除字段 |

## 技术栈

- **CLI 框架**：Click 8.x
- **矢量/栅格 I/O**：GDAL（osgeo）
- **坐标系**：pyproj 3.x
- **空间操作**：Shapely 2.x + GeoPandas 1.x
- **测试**：pytest

## 项目结构

```
gistools/
├── cli/               # CLI 命令入口
│   ├── main.py        # Click group
│   ├── convert.py     # convert 命令组
│   ├── reproject.py   # 坐标系转换
│   ├── buffer.py      # 缓冲区分析
│   ├── analysis.py    # Analysis 工具箱
│   ├── spatial.py     # Spatial Analyst 工具箱
│   └── data.py        # Data Management 工具箱
├── core/              # 核心功能模块
│   ├── formats.py     # 格式检测与转换
│   ├── rasterize.py   # Polygonize/Rasterize 实现
│   ├── dem.py         # DEM 分析（坡度/坡向/山体阴影/等高线）
│   ├── spatial.py     # 空间分析
│   ├── analysis.py    # Analysis 核心（裁剪/交集/合并/融合）
│   ├── data_mgmt.py   # Data Management 核心
│   ├── crs.py         # 坐标系别名
│   └── batch.py       # 批量处理
├── tests/             # pytest 测试
└── docs/              # 设计文档
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.4 | 2026-04-17 | 新增工具箱：analysis / spatial / data（15 个新命令） |
| v0.3 | 2026-04-17 | convert 工具箱扩展（raster2polygon/raster2point/shp2raster/shp2geojson/geojson2shp） |
| v0.2 | 2026-04-17 | buffer 输出格式修复；矢量↔栅格转换报错提示 |
| v0.1 | 2026-04-15 | 初始版本：convert / reproject / buffer |

## License

MIT
