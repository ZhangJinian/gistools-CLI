"""Analysis 工具箱 CLI 测试"""
import pytest
import geopandas as gpd
from shapely.geometry import Point, box
from click.testing import CliRunner
from cli.main import cli
import core.analysis as _core


@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def poly_gdf(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"zone": ["A", "B"], "val": [1, 2]},
        geometry=[box(113.0, 22.0, 114.0, 23.0), box(114.0, 22.0, 115.0, 23.0)],
        crs="EPSG:4326",
    )
    p = tmp_path / "zones.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p, gdf

@pytest.fixture
def overlap_gdf(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"name": ["mask"]},
        geometry=[box(113.5, 22.0, 114.5, 23.0)],
        crs="EPSG:4326",
    )
    p = tmp_path / "mask.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p, gdf

@pytest.fixture
def points_gdf(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"pid": [1, 2]},
        geometry=[Point(113.3, 22.5), Point(113.7, 22.5)],
        crs="EPSG:4326",
    )
    p = tmp_path / "pts.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p, gdf

# --- core unit tests ---

class TestCoreClip:
    def test_clip_basic(self, poly_gdf, overlap_gdf):
        _, features = poly_gdf
        _, mask = overlap_gdf
        result = _core.clip(features, mask)
        assert len(result) == 2
        for geom in result.geometry:
            assert not geom.is_empty

    def test_clip_empty_result(self, poly_gdf):
        _, features = poly_gdf
        far_mask = gpd.GeoDataFrame(geometry=[box(120.0, 30.0, 121.0, 31.0)], crs="EPSG:4326")
        result = _core.clip(features, far_mask)
        assert len(result) == 0

class TestCoreIntersect:
    def test_intersect_basic(self, poly_gdf, overlap_gdf):
        _, features = poly_gdf
        _, other = overlap_gdf
        result = _core.intersect(features, other)
        assert len(result) >= 1

    def test_intersect_no_overlap(self, poly_gdf):
        _, features = poly_gdf
        far = gpd.GeoDataFrame(geometry=[box(120.0, 30.0, 121.0, 31.0)], crs="EPSG:4326")
        result = _core.intersect(features, far)
        assert len(result) == 0

class TestCoreUnion:
    def test_union_basic(self, poly_gdf, overlap_gdf):
        _, a = poly_gdf
        _, b = overlap_gdf
        result = _core.union(a, b)
        assert len(result) == len(a) + len(b)

class TestCoreDissolve:
    def test_dissolve_basic(self, poly_gdf):
        _, features = poly_gdf
        result = _core.dissolve(features, by_field="zone")
        assert set(result["zone"]) == {"A", "B"}

    def test_dissolve_merges(self):
        gdf = gpd.GeoDataFrame(
            {"zone": ["A", "A", "B"]},
            geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(3, 0, 4, 1)],
            crs="EPSG:4326",
        )
        result = _core.dissolve(gdf, by_field="zone")
        assert len(result[result["zone"] == "A"]) == 1

    def test_dissolve_invalid_field(self, poly_gdf):
        _, features = poly_gdf
        with pytest.raises(ValueError, match="不存在"):
            _core.dissolve(features, by_field="nonexistent")

    def test_dissolve_multipart(self):
        gdf = gpd.GeoDataFrame(
            {"zone": ["A", "A"]},
            geometry=[box(0, 0, 1, 1), box(5, 5, 6, 6)],
            crs="EPSG:4326",
        )
        result = _core.dissolve(gdf, by_field="zone", as_multipart=True)
        assert result.geometry.iloc[0].geom_type in ("MultiPolygon", "Polygon")

class TestCoreSpatialJoin:
    def test_spatial_join_left(self, points_gdf, poly_gdf):
        _, pts = points_gdf
        _, zones = poly_gdf
        result = _core.spatial_join(pts, zones, predicate="within", how="left")
        assert len(result) >= len(pts)

    def test_spatial_join_inner(self, points_gdf, poly_gdf):
        _, pts = points_gdf
        _, zones = poly_gdf
        result = _core.spatial_join(pts, zones, predicate="within", how="inner")
        assert len(result) >= 1

# --- CLI end-to-end tests ---

class TestCliClip:
    def test_clip_cmd(self, runner, poly_gdf, overlap_gdf, tmp_path):
        src_p, _ = poly_gdf
        mask_p, _ = overlap_gdf
        out = tmp_path / "clip_out.geojson"
        r = runner.invoke(cli, ["analysis", "clip", str(src_p), str(mask_p), str(out)])
        assert r.exit_code == 0, r.output
        assert out.exists()
        assert len(gpd.read_file(str(out))) > 0

    def test_clip_missing_input(self, runner, overlap_gdf, tmp_path):
        mask_p, _ = overlap_gdf
        r = runner.invoke(cli, [
            "analysis", "clip", "not_exist.shp", str(mask_p), str(tmp_path / "out.geojson")
        ])
        assert r.exit_code != 0

class TestCliIntersect:
    def test_intersect_cmd(self, runner, poly_gdf, overlap_gdf, tmp_path):
        src_p, _ = poly_gdf
        other_p, _ = overlap_gdf
        out = tmp_path / "intersect_out.geojson"
        r = runner.invoke(cli, ["analysis", "intersect", str(src_p), str(other_p), str(out)])
        assert r.exit_code == 0, r.output
        assert out.exists()

    def test_intersect_predicate(self, runner, poly_gdf, overlap_gdf, tmp_path):
        src_p, _ = poly_gdf
        other_p, _ = overlap_gdf
        out = tmp_path / "inter_pred.geojson"
        r = runner.invoke(cli, [
            "analysis", "intersect", str(src_p), str(other_p), str(out),
            "--predicate", "intersects",
        ])
        assert r.exit_code == 0, r.output

class TestCliUnion:
    def test_union_cmd(self, runner, poly_gdf, overlap_gdf, tmp_path):
        src_p, src_gdf = poly_gdf
        other_p, other_gdf = overlap_gdf
        out = tmp_path / "union_out.geojson"
        r = runner.invoke(cli, ["analysis", "union", str(src_p), str(other_p), str(out)])
        assert r.exit_code == 0, r.output
        assert out.exists()
        assert len(gpd.read_file(str(out))) == len(src_gdf) + len(other_gdf)

class TestCliDissolve:
    def test_dissolve_cmd(self, runner, poly_gdf, tmp_path):
        src_p, _ = poly_gdf
        out = tmp_path / "dissolve_out.geojson"
        r = runner.invoke(cli, ["analysis", "dissolve", str(src_p), str(out), "--by", "zone"])
        assert r.exit_code == 0, r.output
        assert out.exists()
        assert set(gpd.read_file(str(out))["zone"]) == {"A", "B"}

    def test_dissolve_missing_by(self, runner, poly_gdf, tmp_path):
        src_p, _ = poly_gdf
        r = runner.invoke(cli, ["analysis", "dissolve", str(src_p), str(tmp_path / "out.geojson")])
        assert r.exit_code == 2

    def test_dissolve_invalid_field(self, runner, poly_gdf, tmp_path):
        src_p, _ = poly_gdf
        r = runner.invoke(cli, [
            "analysis", "dissolve", str(src_p), str(tmp_path / "out.geojson"),
            "--by", "no_such_field",
        ])
        assert r.exit_code == 1

    def test_dissolve_multipart_flag(self, runner, poly_gdf, tmp_path):
        src_p, _ = poly_gdf
        out = tmp_path / "diss_mp.geojson"
        r = runner.invoke(cli, [
            "analysis", "dissolve", str(src_p), str(out), "--by", "zone", "--multipart"
        ])
        assert r.exit_code == 0, r.output

class TestCliSpatialJoin:
    def test_spatial_join_cmd(self, runner, points_gdf, poly_gdf, tmp_path):
        pts_p, _ = points_gdf
        zones_p, _ = poly_gdf
        out = tmp_path / "sjoin_out.geojson"
        r = runner.invoke(cli, [
            "analysis", "spatial-join", str(pts_p), str(zones_p), str(out),
            "--predicate", "within", "--how", "left",
        ])
        assert r.exit_code == 0, r.output
        assert out.exists()
        assert len(gpd.read_file(str(out))) > 0

    def test_spatial_join_inner(self, runner, points_gdf, poly_gdf, tmp_path):
        pts_p, _ = points_gdf
        zones_p, _ = poly_gdf
        out = tmp_path / "sjoin_inner.geojson"
        r = runner.invoke(cli, [
            "analysis", "spatial-join", str(pts_p), str(zones_p), str(out),
            "--predicate", "within", "--how", "inner",
        ])
        assert r.exit_code == 0, r.output

    def test_spatial_join_default(self, runner, points_gdf, poly_gdf, tmp_path):
        pts_p, _ = points_gdf
        zones_p, _ = poly_gdf
        out = tmp_path / "sjoin_def.geojson"
        r = runner.invoke(cli, [
            "analysis", "spatial-join", str(pts_p), str(zones_p), str(out),
        ])
        assert r.exit_code == 0, r.output
