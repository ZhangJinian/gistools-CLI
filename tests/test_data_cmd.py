"""Data Management 工具箱 CLI 测试"""
import pytest
import geopandas as gpd
from click.testing import CliRunner
from shapely.geometry import Point, LineString, Polygon, box
from cli.main import cli
from core import data_mgmt as _core


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def points_gdf(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"name": ["A", "B"], "val": [1, 2]},
        geometry=[Point(114.0, 22.5), Point(113.5, 23.0)],
        crs="EPSG:4326",
    )
    p = tmp_path / "pts.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p, gdf


@pytest.fixture
def lines_gdf(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"name": ["L1", "L2"]},
        geometry=[
            LineString([(113.0, 22.0), (114.0, 22.5), (115.0, 22.0)]),
            LineString([(113.5, 22.5), (114.5, 23.0)]),
        ],
        crs="EPSG:4326",
    )
    p = tmp_path / "lines.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p, gdf


@pytest.fixture
def polys_gdf(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"zone": ["A", "B"], "val": [10, 20]},
        geometry=[
            Polygon([(113.0, 22.0), (114.0, 22.0), (114.0, 23.0), (113.0, 23.0)]),
            Polygon([(114.0, 22.0), (115.0, 22.0), (115.0, 23.0), (114.0, 23.0)]),
        ],
        crs="EPSG:4326",
    )
    p = tmp_path / "polys.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p, gdf


@pytest.fixture
def poly_with_field_gdf(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"region": ["X", "X", "Y"], "area": [100, 200, 300]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(3, 0, 4, 1)],
        crs="EPSG:4326",
    )
    p = tmp_path / "regions.geojson"
    gdf.to_file(str(p), driver="GeoJSON")
    return p, gdf


class TestCoreMerge:
    def test_merge_basic(self, points_gdf, tmp_path):
        p1, _ = points_gdf
        gdf2 = gpd.GeoDataFrame({"name": ["C"], "val": [3]}, geometry=[Point(115.0, 24.0)], crs="EPSG:4326")
        p2 = tmp_path / "pts2.geojson"
        gdf2.to_file(str(p2), driver="GeoJSON")
        out = tmp_path / "merged.geojson"
        count = _core.merge_vectors([p1, p2], out)
        result = gpd.read_file(str(out))
        assert len(result) == 3

    def test_merge_empty(self, tmp_path):
        out = tmp_path / "out.geojson"
        p1 = tmp_path / "empty1.geojson"
        p2 = tmp_path / "empty2.geojson"
        gpd.GeoDataFrame(geometry=[], crs="EPSG:4326").to_file(str(p1), driver="GeoJSON")
        gpd.GeoDataFrame(geometry=[], crs="EPSG:4326").to_file(str(p2), driver="GeoJSON")
        count = _core.merge_vectors([p1, p2], out)
        result = gpd.read_file(str(out))
        assert len(result) == 0


class TestCoreSplit:
    def test_split_basic(self, poly_with_field_gdf, tmp_path):
        p, _ = poly_with_field_gdf
        out_dir = tmp_path / "split_out"
        out_dir.mkdir()
        count = _core.split_by_field(p, out_dir, "region")
        assert count == 2
        assert (out_dir / "X.shp").exists()
        assert (out_dir / "Y.shp").exists()

    def test_split_with_prefix(self, poly_with_field_gdf, tmp_path):
        p, _ = poly_with_field_gdf
        out_dir = tmp_path / "split_out"
        out_dir.mkdir()
        count = _core.split_by_field(p, out_dir, "region", prefix="reg_")
        assert count == 2
        assert (out_dir / "reg_X.shp").exists()
        assert (out_dir / "reg_Y.shp").exists()


class TestCoreFeatureToLine:
    def test_polygon_to_line(self, polys_gdf):
        p, _ = polys_gdf
        import tempfile, os
        out = tempfile.mktemp(suffix=".geojson")
        count = _core.feature_to_line(p, out)
        result = gpd.read_file(out)
        assert all(g.geom_type == "LineString" for g in result.geometry)
        os.unlink(out)

    def test_line_unchanged(self, lines_gdf):
        p, _ = lines_gdf
        import tempfile, os
        out = tempfile.mktemp(suffix=".geojson")
        count = _core.feature_to_line(p, out)
        result = gpd.read_file(out)
        assert all(g.geom_type == "LineString" for g in result.geometry)
        os.unlink(out)


class TestCoreFeatureToPolygon:
    def test_line_to_polygon_open(self, lines_gdf):
        p, _ = lines_gdf
        import tempfile, os
        out = tempfile.mktemp(suffix=".geojson")
        count = _core.feature_to_polygon(p, out)
        result = gpd.read_file(out)
        assert all(g.geom_type == "Polygon" for g in result.geometry)
        os.unlink(out)

    def test_line_to_polygon_closed(self, tmp_path):
        gdf = gpd.GeoDataFrame({"name": ["c"]}, geometry=[LineString([(0, 0), (1, 0), (1, 1), (0, 0)])], crs="EPSG:4326")
        p = tmp_path / "closed.geojson"
        gdf.to_file(str(p), driver="GeoJSON")
        import tempfile, os
        out = tempfile.mktemp(suffix=".geojson")
        count = _core.feature_to_polygon(p, out)
        result = gpd.read_file(out)
        assert all(g.geom_type == "Polygon" for g in result.geometry)
        os.unlink(out)


class TestCoreAddField:
    def test_add_field_string_default(self, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        count = _core.add_field(p, out, "NEW_COL", "STRING")
        result = gpd.read_file(str(out))
        assert "NEW_COL" in result.columns
        assert all(result["NEW_COL"] == "")

    def test_add_field_integer_default(self, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        count = _core.add_field(p, out, "NEW_COL", "INTEGER")
        result = gpd.read_file(str(out))
        assert "NEW_COL" in result.columns
        assert all(result["NEW_COL"] == 0)

    def test_add_field_real_default(self, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        count = _core.add_field(p, out, "NEW_COL", "REAL")
        result = gpd.read_file(str(out))
        assert "NEW_COL" in result.columns
        assert all(result["NEW_COL"] == 0.0)

    def test_add_field_with_value(self, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        count = _core.add_field(p, out, "NEW_COL", "INTEGER", default_value=99)
        result = gpd.read_file(str(out))
        assert all(result["NEW_COL"] == 99)


class TestCoreDeleteField:
    def test_delete_field_basic(self, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        count = _core.delete_field(p, out, "val")
        result = gpd.read_file(str(out))
        assert "val" not in result.columns

    def test_delete_field_not_exist(self, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        with pytest.raises(ValueError, match="不存在"):
            _core.delete_field(p, out, "NONEXISTENT")


class TestCliMerge:
    def test_merge_two_files(self, runner, points_gdf, tmp_path):
        p1, _ = points_gdf
        gdf2 = gpd.GeoDataFrame({"name": ["C"], "val": [3]}, geometry=[Point(115.0, 24.0)], crs="EPSG:4326")
        p2 = tmp_path / "pts2.geojson"
        gdf2.to_file(str(p2), driver="GeoJSON")
        out = tmp_path / "merged.geojson"
        r = runner.invoke(cli, ["data", "merge", str(p1), str(p2), str(out)])
        assert r.exit_code == 0, r.output
        assert out.exists()
        result = gpd.read_file(str(out))
        assert len(result) == 3

    def test_merge_missing_file(self, runner, points_gdf, tmp_path):
        p1, _ = points_gdf
        out = tmp_path / "merged.geojson"
        r = runner.invoke(cli, ["data", "merge", str(p1), "not_exist.shp", str(out)])
        assert r.exit_code == 1
        assert "不存在" in r.output

    def test_merge_one_input(self, runner, points_gdf, tmp_path):
        """只有1个输入+1个输出时，merge视为1个输入到1个输出的直接复制（合法）"""
        p1, _ = points_gdf
        out = tmp_path / "merged.geojson"
        r = runner.invoke(cli, ["data", "merge", str(p1), str(out)])
        assert r.exit_code == 0, r.output
        assert out.exists()


class TestCliSplit:
    def test_split_basic(self, runner, poly_with_field_gdf, tmp_path):
        p, _ = poly_with_field_gdf
        out_dir = tmp_path / "split_out"
        out_dir.mkdir()
        r = runner.invoke(cli, ["data", "split", str(p), str(out_dir), "--by", "region"])
        assert r.exit_code == 0, r.output
        assert (out_dir / "X.shp").exists()
        assert (out_dir / "Y.shp").exists()

    def test_split_with_prefix(self, runner, poly_with_field_gdf, tmp_path):
        p, _ = poly_with_field_gdf
        out_dir = tmp_path / "split_out"
        out_dir.mkdir()
        r = runner.invoke(cli, ["data", "split", str(p), str(out_dir), "--by", "region", "--prefix", "reg_"])
        assert r.exit_code == 0, r.output
        assert (out_dir / "reg_X.shp").exists()
        assert (out_dir / "reg_Y.shp").exists()

    def test_split_missing_by(self, runner, poly_with_field_gdf, tmp_path):
        p, _ = poly_with_field_gdf
        out_dir = tmp_path / "split_out"
        out_dir.mkdir()
        r = runner.invoke(cli, ["data", "split", str(p), str(out_dir)])
        assert r.exit_code == 2


class TestCliFeatureToLine:
    def test_polygon_to_line(self, runner, polys_gdf, tmp_path):
        p, _ = polys_gdf
        out = tmp_path / "boundary.geojson"
        r = runner.invoke(cli, ["data", "feature-to-line", str(p), str(out)])
        assert r.exit_code == 0, r.output
        assert out.exists()
        result = gpd.read_file(str(out))
        assert all(g.geom_type == "LineString" for g in result.geometry)

    def test_line_unchanged(self, runner, lines_gdf, tmp_path):
        p, _ = lines_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "feature-to-line", str(p), str(out)])
        assert r.exit_code == 0, r.output
        result = gpd.read_file(str(out))
        assert all(g.geom_type == "LineString" for g in result.geometry)


class TestCliFeatureToPolygon:
    def test_line_to_polygon(self, runner, lines_gdf, tmp_path):
        p, _ = lines_gdf
        out = tmp_path / "zones.geojson"
        r = runner.invoke(cli, ["data", "feature-to-polygon", str(p), str(out)])
        assert r.exit_code == 0, r.output
        assert out.exists()
        result = gpd.read_file(str(out))
        assert all(g.geom_type == "Polygon" for g in result.geometry)


class TestCliAddField:
    def test_add_field_string(self, runner, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "add-field", str(p), str(out), "--name", "NEW_COL", "--type", "STRING"])
        assert r.exit_code == 0, r.output
        result = gpd.read_file(str(out))
        assert "NEW_COL" in result.columns

    def test_add_field_integer_with_value(self, runner, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "add-field", str(p), str(out), "--name", "SCORE", "--type", "INTEGER", "--value", "42"])
        assert r.exit_code == 0, r.output
        result = gpd.read_file(str(out))
        assert all(result["SCORE"] == 42)

    def test_add_field_real(self, runner, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "add-field", str(p), str(out), "--name", "AREA", "--type", "REAL", "--value", "1.5"])
        assert r.exit_code == 0, r.output
        result = gpd.read_file(str(out))
        assert all(result["AREA"] == 1.5)

    def test_add_field_missing_name(self, runner, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "add-field", str(p), str(out)])
        assert r.exit_code == 2


class TestCliDeleteField:
    def test_delete_field_basic(self, runner, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "delete-field", str(p), str(out), "--name", "val"])
        assert r.exit_code == 0, r.output
        result = gpd.read_file(str(out))
        assert "val" not in result.columns

    def test_delete_field_not_exist(self, runner, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "delete-field", str(p), str(out), "--name", "NONEXISTENT"])
        assert r.exit_code == 1
        assert "不存在" in r.output

    def test_delete_field_missing_name(self, runner, points_gdf, tmp_path):
        p, _ = points_gdf
        out = tmp_path / "out.geojson"
        r = runner.invoke(cli, ["data", "delete-field", str(p), str(out)])
        assert r.exit_code == 2
