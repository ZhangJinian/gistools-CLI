# GISTools CLI — 更新记录

> 每次重要变更后更新此文件。

---

## 版本 v0.3（开发中）

**日期：** 2026-04-17
**状态：** 🚧 开发中

### 本期工作：convert 工具箱扩展

将 `gistools convert` 改造为 Click Group，作为转换工具箱入口，新增以下子命令：

| 子命令 | 功能 | GDAL 实现 |
|--------|------|-----------|
| `gistools convert raster2polygon` | 栅格 → 面要素 | `gdal.Polygonize()` |
| `gistools convert raster2point` | 栅格 → 点要素 | `gdal.Open()` 遍历像元中心 |
| `gistools convert shp2raster` | 矢量(SHP) → 栅格(TIFF) | `gdal.Rasterize()` |
| `gistools convert shp2geojson` | SHP → GeoJSON | `ogr.CopyDataSource()` |
| `gistools convert geojson2shp` | GeoJSON → SHP | `ogr.CopyDataSource()` |

#### raster2polygon 参数（参考 ArcGIS Raster To Polygon）

```bash
gistools convert raster2polygon <input_raster> <output_polygon>
    [--field <字段名>]        # 写入属性表的栅格值字段，默认 "DN"
    [--simplify <容差>]       # 几何简化容差（GDAL单位），默认不简化
    [--multi]                 # 输出多部件（MultiPatch/Polygon），默认否
```

#### raster2point 参数（参考 ArcGIS Raster To Point）

```bash
gistools convert raster2point <input_raster> <output_point>
    [--field <字段名>]        # 像元值写入的字段，默认 "value"
```

#### shp2raster 参数（参考 ArcGIS Feature To Raster）

```bash
gistools convert shp2raster <input_shp> <output_raster>
    --cellsize <数值>          # 必填，像元大小
    [--field <字段名>]         # 用于填入栅格的字段，默认填 1
    [--extent <xmin ymin xmax ymax>]  # 输出范围，默认从矢量外包计算
```

#### shp2geojson 参数（ArcGIS 无直接对应，用 GDAL）

```bash
gistools convert shp2geojson <input_shp> <output_geojson>
    [--encoding <编码>]        # 编码，默认 UTF-8
```

#### geojson2shp 参数（ArcGIS 无直接对应，用 GDAL）

```bash
gistools convert geojson2shp <input_geojson> <output_shp>
    [--encoding <编码>]        # 编码，默认 UTF-8
```

---

## 版本 v0.2

**日期：** 2026-04-17
**Tag:** `v0.2`

| Commit | 变更 |
|--------|------|
| 7043fbc | fix: buffer输出格式根据扩展名确定；矢量↔栅格转换给出明确错误提示 |

**命令：** convert / reproject / buffer（原有功能不变）

---

## 版本 v0.1

**日期：** 2026-04-15
**Tag:** `v0.1`

| Commit | 变更 |
|--------|------|
| f280c2e | test: 原型 v0.1 完成，45 项测试全部通过 |
| 5e8f08f | feat: gistools buffer 命令（含栅格拒绝 + dissolve） |
| 5000171 | feat: gistools reproject 命令（含中文别名 + 无CRS报错） |
| c2e3982 | feat: 坐标系别名库（中英文 + EPSG 编码） |
| 7435020 | feat: gistools convert 命令（单文件+批量） |
| 6ac24c7 | feat: 批量处理基础设施（文件收集 + 错误汇报） |
| 6577d50 | feat: 格式检测与单文件矢量/栅格转换 |
| 90e6e0d | chore: 项目骨架 + CLI 入口 |

**初始命令：** convert / reproject / buffer
