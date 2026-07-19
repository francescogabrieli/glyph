from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ..core.models import CompressionProfile


class GlyphPaths(BaseModel):
    source: str | None = None
    manifest: str | None = None
    rules: str | None = None


class GlyphConfig(BaseModel):
    version: str = "0.1"
    default_profile: str | None = None
    min_semantic_coverage: float | None = None
    min_operational_coverage: float | None = None
    min_reduction: float | None = None
    max_unmapped: int | None = None
    paths: GlyphPaths = GlyphPaths()
    path: Path | None = None

    def profile(self) -> CompressionProfile | None:
        if self.default_profile is None:
            return None
        try:
            return CompressionProfile(self.default_profile)
        except ValueError as exc:
            allowed = ", ".join(profile.value for profile in CompressionProfile)
            raise ValueError(f"Invalid default_profile in {self.path}: expected one of: {allowed}.") from exc


def find_config(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for directory in [current, *current.parents]:
        candidate = directory / ".glyph" / "config.toml"
        if candidate.exists():
            return candidate
    return None


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        raise ValueError("empty value")
    if value[0] in {"\"", "'"}:
        if len(value) < 2 or value[-1] != value[0]:
            raise ValueError(f"unterminated string {raw!r}")
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"unsupported TOML value {raw!r}") from exc


def _minimal_toml_loads(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current = data
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            if not section:
                raise ValueError(f"empty section at line {line_no}")
            current = data
            for part in section.split("."):
                current = current.setdefault(part, {})
                if not isinstance(current, dict):
                    raise ValueError(f"invalid section {section!r} at line {line_no}")
            continue
        if "=" not in line:
            raise ValueError(f"expected key = value at line {line_no}")
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty key at line {line_no}")
        current[key] = _parse_scalar(raw_value)
    return data


def _load_toml(text: str) -> dict[str, Any]:
    try:
        import tomllib

        return tomllib.loads(text)
    except ModuleNotFoundError:
        return _minimal_toml_loads(text)
    except Exception as exc:
        raise ValueError(str(exc)) from exc


def load_config(path: Path | None = None, start: Path | None = None) -> GlyphConfig | None:
    config_path = path or find_config(start)
    if config_path is None:
        return None
    try:
        raw = _load_toml(config_path.read_text(encoding="utf-8"))
        config = GlyphConfig.model_validate(raw)
        config.path = config_path
        config.profile()
        return config
    except OSError as exc:
        raise ValueError(f"Could not read config {config_path}: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Could not parse config {config_path}: {exc}") from exc


def default_config_text(source: str = "AGENTS.md", manifest: str = "AGENTS.glp") -> str:
    return (
        'version = "0.1"\n'
        'default_profile = "compact"\n'
        "min_semantic_coverage = 95\n"
        "min_operational_coverage = 80\n"
        "min_reduction = 20\n"
        "max_unmapped = 10\n"
        "\n"
        "[paths]\n"
        f'source = "{source}"\n'
        f'manifest = "{manifest}"\n'
    )
