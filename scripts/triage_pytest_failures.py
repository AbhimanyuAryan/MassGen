#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]


_RE_ABS_PATH = re.compile(r"(/[^ \n\t:]+)+")
_RE_LINE_NO = re.compile(r"(line\s+)\d+")
_RE_HEX = re.compile(r"\b0x[0-9a-fA-F]+\b")
_RE_FLOAT = re.compile(r"\b\d+\.\d+\b")
_RE_INT = re.compile(r"\b\d+\b")
_RE_PY_FRAME = re.compile(r'File "([^"]+)", line (\d+), in ([^\n]+)')


def _short_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


def _relativize_paths(s: str) -> str:
    def repl(m: re.Match) -> str:
        p = m.group(0)
        try:
            rp = str(Path(p).resolve().relative_to(ROOT))
            return rp
        except Exception:
            return "<path>"

    return _RE_ABS_PATH.sub(repl, s)


def _normalize_message(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    s = _relativize_paths(s)
    s = _RE_HEX.sub("<hex>", s)
    s = _RE_LINE_NO.sub(r"\1<line>", s)
    # Keep small integers (often meaningful), but squash large ones to reduce noise.
    s = _RE_FLOAT.sub("<num>", s)
    s = _RE_INT.sub(lambda m: m.group(0) if len(m.group(0)) <= 2 else "<n>", s)
    return s


def _extract_top_frames(text: str, limit: int = 5) -> List[str]:
    frames: List[str] = []
    for m in _RE_PY_FRAME.finditer(text or ""):
        f = m.group(1)
        try:
            rp = str(Path(f).resolve().relative_to(ROOT))
        except Exception:
            rp = f
        frames.append(f"{rp}:{m.group(2)} in {m.group(3).strip()}")
        if len(frames) >= limit:
            break
    return frames


def _suspect_files_from_frames(frames: Iterable[str]) -> List[str]:
    out: List[str] = []
    for fr in frames:
        path = fr.split(":", 1)[0]
        if path.startswith(("massgen/", "scripts/")) and path not in out:
            out.append(path)
    return out


@dataclass
class FailureCase:
    nodeid: str
    file: str
    classname: str
    name: str
    kind: str  # failure|error|skipped? (we only ingest failure/error)
    exc_type: str
    message: str
    text: str


@dataclass
class Cluster:
    key: str
    exc_type: str
    norm_message: str
    cases: List[FailureCase] = field(default_factory=list)
    frames: List[str] = field(default_factory=list)
    suspect_files: List[str] = field(default_factory=list)


def _looks_like_class_name(s: str) -> bool:
    if not s:
        return False
    if s.startswith("Test"):
        return True
    # Heuristic: class names usually start with an uppercase char.
    return s[0].isupper() and not s.startswith("test_")


def _module_to_relpath(module: str) -> str:
    return module.replace(".", "/") + ".py"


def _normalize_file_attr_to_relpath(file_attr: str) -> str:
    file_attr = (file_attr or "").strip()
    if not file_attr:
        return ""
    p = Path(file_attr)
    try:
        rp = str(p.resolve().relative_to(ROOT))
        return rp.replace("\\", "/")
    except Exception:
        # If it's already a relative path inside repo, keep as-is.
        return file_attr.replace("\\", "/")


def _infer_pytest_nodeid(file_attr: str, classname: str, name: str) -> str:
    """
    Convert JUnit testcase metadata to a pytest-style nodeid:
    - massgen/tests/test_x.py::TestClass::test_name
    """
    file_rel = _normalize_file_attr_to_relpath(file_attr)

    class_name = ""
    module_part = (classname or "").strip()
    if module_part:
        parts = module_part.split(".")
        if len(parts) >= 2 and _looks_like_class_name(parts[-1]):
            class_name = parts[-1]
            module_part = ".".join(parts[:-1])

    # If file attr is missing, infer path from module part.
    if not file_rel and module_part:
        file_rel = _module_to_relpath(module_part)

    # Fall back to raw classname if we still have nothing.
    if not file_rel:
        file_rel = (classname or "").replace(".", "/")

    file_rel = file_rel.replace("\\", "/")

    node_parts = [file_rel]
    if class_name:
        node_parts.append(class_name)
    if name:
        node_parts.append(name)
    return "::".join(node_parts)


def _iter_failures(junit_xml: Path) -> Iterable[FailureCase]:
    tree = ET.parse(junit_xml)
    root = tree.getroot()

    # Support <testsuite> root or <testsuites>.
    testcases = root.findall(".//testcase")
    for tc in testcases:
        file = tc.attrib.get("file") or ""
        classname = tc.attrib.get("classname", "")
        name = tc.attrib.get("name", "")

        failure = tc.find("failure")
        error = tc.find("error")
        elem = failure if failure is not None else error
        if elem is None:
            continue

        kind = "failure" if failure is not None else "error"
        exc_type = (elem.attrib.get("type") or "").strip() or "<unknown>"
        message = (elem.attrib.get("message") or "").strip()
        text = (elem.text or "").strip()

        nodeid = _infer_pytest_nodeid(file_attr=file, classname=classname, name=name)
        yield FailureCase(
            nodeid=nodeid,
            file=file,
            classname=classname,
            name=name,
            kind=kind,
            exc_type=exc_type,
            message=message,
            text=text,
        )


def cluster_failures(cases: Iterable[FailureCase]) -> List[Cluster]:
    by_key: Dict[str, Cluster] = {}
    for c in cases:
        norm = _normalize_message(
            c.message or c.text.splitlines()[:1][0] if c.text else ""
        )
        key = f"{c.exc_type}::{norm}"
        if key not in by_key:
            by_key[key] = Cluster(key=key, exc_type=c.exc_type, norm_message=norm)
        by_key[key].cases.append(c)

    clusters = list(by_key.values())
    clusters.sort(key=lambda cl: (-len(cl.cases), cl.exc_type, cl.norm_message))

    for cl in clusters:
        # Prefer frames from the first case's text; it's usually the richest.
        seed = cl.cases[0].text or ""
        cl.frames = _extract_top_frames(seed, limit=6)
        cl.suspect_files = _suspect_files_from_frames(cl.frames)
    return clusters


def render_summary(clusters: List[Cluster], out_dir: Path) -> None:
    total = sum(len(c.cases) for c in clusters)
    lines = [
        "# Pytest failure triage summary",
        "",
        f"- JUnit source: `{out_dir.name}/...`",
        f"- Total failing testcases (errors+failures): **{total}**",
        f"- Distinct clusters: **{len(clusters)}**",
        "",
        "## Top clusters",
        "",
    ]

    for i, cl in enumerate(clusters[:50], start=1):
        cid = _short_id(cl.key)
        lines.append(
            f"{i}. **{len(cl.cases)}×** `{cl.exc_type}` — `{cl.norm_message[:120]}` ([packet](tasks/cluster_{cid}.md))"
        )

    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_task_packet(cluster: Cluster, out_dir: Path) -> None:
    cid = _short_id(cluster.key)
    tasks_dir = out_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    nodeids = [c.nodeid for c in cluster.cases]
    nodeids_preview = nodeids[:25]

    repro_single = (
        f"/Users/admin/src/MassGen/.venv/bin/python -m pytest -q {nodeids_preview[0]}"
    )
    repro_cluster = (
        "/Users/admin/src/MassGen/.venv/bin/python -m pytest -q "
        + " ".join(nodeids_preview)
    )

    md = [
        f"# Cluster {cid}",
        "",
        f"- **Count**: {len(cluster.cases)}",
        f"- **Exception type**: `{cluster.exc_type}`",
        f"- **Normalized message**: `{cluster.norm_message}`",
        "",
        "## Minimal repro",
        "",
        "Single failing test:",
        "",
        "```bash",
        repro_single,
        "```",
        "",
        "Up to 25 tests from this cluster:",
        "",
        "```bash",
        repro_cluster,
        "```",
        "",
        "## Affected nodeids",
        "",
        *[f"- `{n}`" for n in nodeids_preview],
    ]
    if len(nodeids) > len(nodeids_preview):
        md += [
            "",
            f"_… plus {len(nodeids) - len(nodeids_preview)} more in this cluster._",
        ]

    if cluster.frames:
        md += ["", "## Top stack frames (from first failure)", ""]
        md += ["```", *cluster.frames, "```"]

    if cluster.suspect_files:
        md += ["", "## Suspect files", ""]
        md += [*([f"- `{p}`" for p in cluster.suspect_files])]

    md += [
        "",
        "## Suggested next step (for the subagent)",
        "",
        "- Confirm if this is **unit** vs **integration/docker/expensive**.",
        "- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.",
        "- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.",
        "",
    ]

    (tasks_dir / f"cluster_{cid}.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Cluster pytest failures from a JUnit XML report."
    )
    ap.add_argument(
        "--junit-xml", required=True, help="Path to pytest --junitxml output."
    )
    ap.add_argument(
        "--out-dir",
        default=str(ROOT / ".cursor" / "triage"),
        help="Output directory for triage summary + task packets (default: .cursor/triage).",
    )
    args = ap.parse_args()

    junit_xml = Path(args.junit_xml).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = list(_iter_failures(junit_xml))
    clusters = cluster_failures(cases)

    render_summary(clusters, out_dir)
    for cl in clusters:
        render_task_packet(cl, out_dir)

    print(f"Wrote {len(clusters)} cluster packets to: {out_dir / 'tasks'}")
    print(f"Summary: {out_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
