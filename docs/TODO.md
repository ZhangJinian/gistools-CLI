# GISTools CLI — 工作清单

> 版本：v0.4（开发中）
> 更新日期：2026-04-17

---

## v0.4 开发计划

### Task #24 — Analysis 工具箱

**状态：** 🟡 开发中

**命令：**

| 命令 | 功能 | 核心实现 |
|------|------|---------|
| `gistools clip` | 裁剪（输入要素按裁剪图层切） | Shapely `intersection` |
| `gistools intersect` | 交集（多要素相交） | Shapely `intersection` |
| `gistools union` | 合并（保留全部） | Shapely `unary_union` / GeoPandas `overlay` |
| `gistools dissolve` | 融合（按字段合并相邻多边形） | GeoPandas `dissolve` |
| `gistools spatial-join` | 空间连接（基于空间关系关联属性） | GeoPandas `sjoin` |

**参考：** ArcGIS Analysis Toolbox 参数规范

---

### Task #25 — Spatial Analyst 工具箱

**状态：** 🔴 待开始

**命令：**

| 命令 | 功能 | 核心实现 |
|------|------|---------|
| `gistools slope` | 坡度分析（度或百分比） | GDAL DEMProcessing / RichDEM |
| `gistools aspect` | 坡向分析（方位角） | GDAL DEMProcessing / RichDEM |
| `gistools hillshade` | 山体阴影 | GDAL DEMProcessing |
| `gistools contour` | 等高线生成 | GDAL `gdal_contour` |

**参考：** ArcGIS Spatial Analyst Toolbox 参数规范

---

### Task #26 — Data Management 工具箱

**状态：** 🔴 待开始

**命令：**

| 命令 | 功能 | 核心实现 |
|------|------|---------|
| `gistools merge` | 合并多个矢量文件 | GeoPandas `pd.concat` |
| `gistools split` | 按字段或位置分割矢量 | GeoPandas groupby |
| `gistools feature-to-line` | 面/线要素转线 | Shapely `exterior` |
| `gistools feature-to-polygon` | 线要素转面 | Shapely `Polygon` |
| `gistools add-field` | 添加字段 | GeoPandas `assign` |
| `gistools delete-field` | 删除字段 | GeoPandas `drop` |

**参考：** ArcGIS Data Management Toolbox 参数规范

---

### Task #27 — 文档更新 + v0.4 发布

**状态：** 🔴 待开始

**内容：**
- 更新 `docs/DESIGN.md` — 新增三个工具箱的设计文档
- 更新 `docs/CHANGELOG.md` — 记录 v0.4 变更
- 更新 `README.md` / `README_CN.md` — 新增命令说明
- Git commit + tag v0.4 + push

---

## v0.3 完成记录（2026-04-17）

| 命令 | 功能 | 核心 GDAL 函数 |
|------|------|---------------|
| `gistools convert raster2polygon` | 栅格 → 面要素 | `gdal.Polygonize()` |
| `gistools convert raster2point` | 栅格 → 点要素 | GDAL 遍历像元中心 |
| `gistools convert shp2raster` | 矢量 → 栅格 | `gdal.Rasterize()` |
| `gistools convert shp2geojson` | SHP → GeoJSON | `ogr.CopyDataSource()` |
| `gistools convert geojson2shp` | GeoJSON → SHP | `ogr.CopyDataSource()` |
