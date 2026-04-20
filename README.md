# GISTools CLI

A command-line toolkit for GIS professionals and developers, wrapping common GIS operations into standard CLI commands.

## Installation

**Development:**
```bash
pip install -e .
```

**Requirements:** Python 3.9+ / GDAL 2.4+

## Quick Start

```bash
# Show all commands
gistools --help

# convert toolbox
gistools convert --help

# raster2polygon — Raster to polygon
gistools convert raster2polygon input.tif output.shp --field DN

# raster2point — Raster to point
gistools convert raster2point input.tif output.shp

# shp2raster — Vector to raster
gistools convert shp2raster input.shp output.tif --cellsize 30

# shp2geojson — SHP to GeoJSON
gistools convert shp2geojson input.shp output.geojson

# geojson2shp — GeoJSON to SHP
gistools convert geojson2shp input.geojson output.shp

# Coordinate system transformation
gistools reproject input.shp output.shp --to WGS84

# Buffer analysis
gistools buffer input.shp output.shp --distance 100 --unit meters

# Analysis toolbox
gistools analysis clip input.shp clip_zone.shp output.shp
gistools analysis intersect a.shp b.shp output.shp
gistools analysis union a.shp b.shp output.shp
gistools analysis dissolve zones.shp dissolved.shp --by region
gistools analysis spatial-join points.shp zones.shp joined.shp --predicate intersects --how left

# Spatial Analyst toolbox
gistools spatial slope dem.tif slope.tif
gistools spatial aspect dem.tif aspect.tif
gistools spatial hillshade dem.tif hillshade.tif
gistools spatial contour dem.tif contour.shp --interval 10

# Data Management toolbox
gistools data merge a.shp b.shp output.shp
gistools data split zones.shp out_dir/ --by region
gistools data feature-to-line polygons.shp lines.shp
gistools data feature-to-polygon lines.shp polygons.shp
gistools data add-field input.shp output.shp --name new_field --type REAL --value 0
gistools data delete-field input.shp output.shp --name unused_field
```

## Features

| Command | Description |
|---------|-------------|
| `gistools convert raster2polygon` | Raster → Polygon (gdal.Polygonize) |
| `gistools convert raster2point` | Raster → Point (pixel center traversal) |
| `gistools convert shp2raster` | Vector → Raster (gdal.Rasterize) |
| `gistools convert shp2geojson` | SHP → GeoJSON |
| `gistools convert geojson2shp` | GeoJSON → SHP |
| `gistools reproject` | Coordinate system transformation (EPSG / Chinese aliases) |
| `gistools buffer` | Buffer analysis (meters / km / degrees) |
| `gistools analysis clip` | Clip features by polygon |
| `gistools analysis intersect` | Intersect two layers |
| `gistools analysis union` | Union two layers |
| `gistools analysis dissolve` | Dissolve by field |
| `gistools analysis spatial-join` | Spatial join |
| `gistools spatial slope` | Slope analysis (degrees / percent) |
| `gistools spatial aspect` | Aspect analysis |
| `gistools spatial hillshade` | Hillshade |
| `gistools spatial contour` | Contour lines |
| `gistools data merge` | Merge multiple vector files |
| `gistools data split` | Split by field |
| `gistools data feature-to-line` | Polygon/line → line |
| `gistools data feature-to-polygon` | Line → polygon |
| `gistools data add-field` | Add field |
| `gistools data delete-field` | Delete field |

## Tech Stack

- **CLI Framework**: Click 8.x
- **Vector/Raster I/O**: GDAL (osgeo)
- **Coordinate Systems**: pyproj 3.x
- **Spatial Operations**: Shapely 2.x + GeoPandas 1.x
- **Testing**: pytest

## Project Structure

```
gistools/
├── cli/               # CLI entry points
│   ├── main.py        # Click group
│   ├── convert.py     # convert command group
│   ├── reproject.py   # Coordinate transformation
│   ├── buffer.py      # Buffer analysis
│   ├── analysis.py    # Analysis toolbox
│   ├── spatial.py     # Spatial Analyst toolbox
│   └── data.py        # Data Management toolbox
├── core/              # Core modules
│   ├── formats.py     # Format detection and conversion
│   ├── rasterize.py   # Polygonize/Rasterize implementation
│   ├── dem.py         # DEM analysis (slope/aspect/hillshade/contour)
│   ├── spatial.py     # Spatial analysis
│   ├── analysis.py    # Analysis core (clip/intersect/union/dissolve)
│   ├── data_mgmt.py   # Data management core
│   ├── crs.py         # Coordinate system aliases
│   └── batch.py       # Batch processing
├── tests/             # pytest tests
└── docs/              # Design documents
```

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v0.4 | 2026-04-17 | New toolboxes: analysis, spatial, data (15 new commands) |
| v0.3 | 2026-04-17 | convert toolbox extension (raster2polygon/raster2point/shp2raster/shp2geojson/geojson2shp) |
| v0.2 | 2026-04-17 | buffer output format fix; vector↔raster conversion error messages |
| v0.1 | 2026-04-15 | Initial release: convert / reproject / buffer |

## License

MIT
