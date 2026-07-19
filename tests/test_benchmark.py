from pathlib import Path

from glyph.governance.benchmark import benchmark_real, run_benchmark


def test_benchmark_report_generation():
    result = run_benchmark(Path("benchmarks"))
    assert len(result["cases"]) >= 10
    assert Path("benchmarks/benchmark-report.json").exists()
    assert result["average_coverage"] >= 0.9


def test_real_benchmark_discovery(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Always run tests before completion. `pytest`", encoding="utf-8")
    result = benchmark_real(tmp_path)
    assert result["files_discovered"] == 1
    assert result["files_compiled"] == 1
