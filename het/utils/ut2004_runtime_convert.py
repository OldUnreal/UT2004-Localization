#!/usr/bin/env python3
from __future__ import annotations
import argparse, codecs, hashlib, re, sys
from pathlib import Path
from typing import Dict, List, Tuple

USER_CONFIG = {
    "output_mode": "suffix",
    "output_suffix": ".runtime",
    "default_outdir": "runtime_out",
    "write_utf16le_bom": True,
    "verbose_overrides": True,
    "show_samples": True,
    "default_reverse_runtime": True,
    "preserve_untranslated_english": True,
    "warn_untranslated_english": True,
}

FILE_RULES = {"GUI2K4.het": {"reverse_runtime": True}}
COPY_RUNTIME_REFERENCE_FILES = {}

LINE_OVERRIDES: Dict = {}

RUNTIME_PREFIX_OVERRIDES: Dict = {
    "Engine.het": [
        ('MessageNoAmmo=', 'MessageNoAmmo="חסר תחמושת "'),
    ],
}

RUNTIME_LINE_NUMBER_OVERRIDES: Dict = {}

MIXED_COMPOUND_NORMALIZATION = {
  "ה-Shock Rifle": "Shock Rifle-ה",
  "ה-Super Shock Rifle": "Super Shock Rifle-ה",
  "ה-Flak Cannon": "Flak Cannon-ה",
  "ה-Bio-Rifle": "Bio-Rifle-ה",
  "ה-Rocket Launcher": "Rocket Launcher-ה",
  "ה-Lightning Gun": "Lightning Gun-ה",
  "ה-Link Gun": "Link Gun-ה",
  "ה-Shield Gun": "Shield Gun-ה",
  "ה-Assault Rifle": "Assault Rifle-ה",
  "ה-Sniper Rifle": "Sniper Rifle-ה",
  "ה-Minigun": "Minigun-ה",
  "ה-Ion Painter": "Ion Painter-ה",
  "ה-Redeemer": "Redeemer-ה",
  "ה-Translocator": "Translocator-ה",
  "מ-UT2004": "UT2004-מ",
  "ל-UT2004": "UT2004-ל",
  "ב-UT2004": "UT2004-ב"
}

def read_text_auto(path: Path):
    raw = path.read_bytes()
    if raw.startswith(codecs.BOM_UTF16_LE):
        return raw[len(codecs.BOM_UTF16_LE):].decode("utf-16le"), "utf-16le-bom"
    if raw.startswith(codecs.BOM_UTF8):
        return raw[len(codecs.BOM_UTF8):].decode("utf-8"), "utf-8-bom"
    for enc in ("utf-16", "utf-8", "latin1"):
        try:
            return raw.decode(enc), enc
        except Exception:
            pass
    raise UnicodeError(f"Could not decode {path}")

def write_text_utf16le_bom(path: Path, text: str):
    path.write_bytes(codecs.BOM_UTF16_LE + text.encode("utf-16le"))

ASCII_WORD = r"[A-Za-z0-9_:+~()/]+(?:[.-][A-Za-z0-9_:+~()/]+)*"
ASCII_PHRASE = rf"{ASCII_WORD}(?: {ASCII_WORD})*"
HEBREW_WORD = r"[\u05D0-\u05EA]+"
COMPOUND_RE = re.compile(rf"({HEBREW_WORD})-({ASCII_PHRASE})")
PLACEHOLDER_RE = (
    r"%%[A-Za-z0-9_]+|"
    r"%[A-Za-z0-9:_]+(?: [0-9]+)?%|"
    r"%[0-9]+(?:\.[0-9]+)?[A-Za-z]|"
    r"%[A-Za-z][A-Za-z0-9_]*|"
    r"%[A-Za-z]"
)
TOKEN_RE = re.compile(
    rf"({PLACEHOLDER_RE}|"
    rf"\[[A-Za-z0-9_./:+~ -]+\]|"
    rf"{ASCII_PHRASE}-{HEBREW_WORD}|"
    rf"[+-]?[0-9]+(?::[0-9]+)?(?:x[0-9]+)?|"
    rf"{ASCII_PHRASE})"
)
QUOTED_SEGMENT_RE = re.compile(r'"([^"]*)"')

def normalize_mixed_compounds(text: str) -> str:
    for src, dst in MIXED_COMPOUND_NORMALIZATION.items():
        text = text.replace(src, dst)
    return COMPOUND_RE.sub(lambda m: f"{m.group(2)}-{m.group(1)}", text)

HEBREW_CHAR_RE = re.compile(r"[\u05D0-\u05EA]")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")

def should_preserve_untranslated_english(text: str) -> bool:
    if not USER_CONFIG.get("preserve_untranslated_english", True):
        return False
    has_hebrew = bool(HEBREW_CHAR_RE.search(text))
    has_ascii = bool(ASCII_LETTER_RE.search(text))
    return has_ascii and not has_hebrew

def reverse_runtime_text(text: str) -> str:
    text = normalize_mixed_compounds(text)
    parts=[]; i=0
    for m in TOKEN_RE.finditer(text):
        if m.start() > i:
            parts.append(("txt", text[i:m.start()]))
        parts.append(("tok", m.group(0)))
        i = m.end()
    if i < len(text):
        parts.append(("txt", text[i:]))
    return "".join(v if k=="tok" else v[::-1] for k,v in reversed(parts))

def convert_quoted_segments(line: str) -> str:
    warnings: List[str] = []
    def normalize_inner_ascii_quotes(content: str) -> str:
        return re.sub(r'(?<=[\u05D0-\u05EA])"(?=[\u05D0-\u05EA])', '״', content)
    def convert_content(content: str) -> str:
        content = normalize_inner_ascii_quotes(content)
        if should_preserve_untranslated_english(content):
            if USER_CONFIG.get("warn_untranslated_english", True):
                warnings.append(content[:80])
            return content
        return reverse_runtime_text(content)
    def repl(m):
        return '"' + convert_content(m.group(1)) + '"'
    out = QUOTED_SEGMENT_RE.sub(repl, line)
    if warnings:
        setattr(convert_quoted_segments, "_last_warnings", warnings)
    else:
        setattr(convert_quoted_segments, "_last_warnings", [])
    return out

def file_reverse_runtime_enabled(path: Path) -> bool:
    rule = FILE_RULES.get(path.name, {})
    return rule.get("reverse_runtime", USER_CONFIG["default_reverse_runtime"])

def apply_line_overrides(path: Path, lines: List[str]):
    overrides = LINE_OVERRIDES.get(path.name, [])
    if not overrides:
        return lines, []
    out=[]; hits=[]
    for line in lines:
        replaced=False
        for starts_with, replacement in overrides:
            if line.startswith(starts_with):
                out.append(replacement)
                hits.append(starts_with)
                replaced=True
                break
        if not replaced:
            out.append(line)
    return out, hits

def apply_runtime_line_number_overrides(path: Path, runtime_lines: List[str], source_lines: List[str]):
    mapping = RUNTIME_LINE_NUMBER_OVERRIDES.get(path.name, {})
    if not mapping:
        return runtime_lines, []
    out = list(runtime_lines)
    hits = []
    for k, replacement in mapping.items():
        idx = int(k) - 1
        src_line = source_lines[idx] if 0 <= idx < len(source_lines) else ""
        src_has_hebrew = bool(HEBREW_CHAR_RE.search(src_line))
        if not src_has_hebrew:
            continue
        while idx >= len(out):
            out.append("")
        out[idx] = replacement
        hits.append(str(k))
    return out, hits

def transform_file(path: Path, outdir: Path | None = None):
    text, detected_encoding = read_text_auto(path)
    lines = text.splitlines()
    reverse_enabled = file_reverse_runtime_enabled(path)
    lines, override_hits = apply_line_overrides(path, lines)

    english_preserve_hits: List[str] = []
    runtime_lines = []
    if reverse_enabled:
        for line in lines:
            converted = convert_quoted_segments(line)
            runtime_lines.append(converted)
            english_preserve_hits.extend(getattr(convert_quoted_segments, "_last_warnings", []))
    else:
        runtime_lines = list(lines)

    runtime_prefix_hits = []
    runtime_prefix_overrides = RUNTIME_PREFIX_OVERRIDES.get(path.name, [])
    if runtime_prefix_overrides:
        new_runtime_lines = []
        for line in runtime_lines:
            replaced = False
            for starts_with, replacement in runtime_prefix_overrides:
                if line.startswith(starts_with):
                    new_runtime_lines.append(replacement)
                    runtime_prefix_hits.append(starts_with)
                    replaced = True
                    break
            if not replaced:
                new_runtime_lines.append(line)
        runtime_lines = new_runtime_lines

    runtime_lines, runtime_hits = apply_runtime_line_number_overrides(path, runtime_lines, lines)
    override_hits = override_hits + runtime_prefix_hits + runtime_hits
    runtime_text = "\n".join(runtime_lines) + "\n"

    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        out_path = outdir / path.name
    elif USER_CONFIG["output_mode"] == "inplace":
        out_path = path
    elif USER_CONFIG["output_mode"] == "outdir":
        target_dir = Path(USER_CONFIG["default_outdir"])
        target_dir.mkdir(parents=True, exist_ok=True)
        out_path = target_dir / path.name
    else:
        out_path = path.with_name(path.stem + USER_CONFIG["output_suffix"] + path.suffix)

    write_text_utf16le_bom(out_path, runtime_text)
    sha = hashlib.sha256(runtime_text.encode("utf-16le")).hexdigest()
    sample_before = next((line for line in lines if '"' in line), None)
    sample_after = next((line for line in runtime_lines if '"' in line), None)
    info = {
        "source": str(path),
        "target": str(out_path),
        "encoding_in": detected_encoding,
        "reverse_runtime": reverse_enabled,
        "override_hits": override_hits,
        "english_preserve_hits": english_preserve_hits,
        "sample_before": sample_before,
        "sample_after": sample_after,
        "sha256": sha,
    }
    return out_path, info

def parse_args(argv):
    p = argparse.ArgumentParser(description="Convert UT2004 Hebrew masters into runtime files for zero-RTL renderer.")
    p.add_argument("files", nargs="+", help="Input files")
    p.add_argument("--outdir", help="Output directory")
    p.add_argument("--no-samples", action="store_true")
    p.add_argument("--quiet", action="store_true")
    return p.parse_args(argv)

def main(argv):
    args = parse_args(argv)
    if args.no_samples:
        USER_CONFIG["show_samples"] = False
    outdir = Path(args.outdir) if args.outdir else None
    ok=0; bad=0
    for raw in args.files:
        path = Path(raw)
        if not path.exists():
            print(f"[ERROR] missing: {path}", file=sys.stderr)
            bad += 1
            continue
        if path.is_dir():
            print(f"[SKIP] directory: {path}")
            continue
        try:
            out_path, info = transform_file(path, outdir=outdir)
            ok += 1
            if not args.quiet:
                print(f"[OK] {path} -> {out_path}")
                print(f"     input-encoding: {info['encoding_in']}")
                print(f"     reverse-runtime: {info['reverse_runtime']}")
                if USER_CONFIG["verbose_overrides"] and info["override_hits"]:
                    print(f"     overrides-hit: {', '.join(info['override_hits'])}")
                if info["english_preserve_hits"]:
                    preview = " | ".join(info["english_preserve_hits"][:3])
                    print(f"     preserved-untranslated-english: {preview}")
                if USER_CONFIG["show_samples"] and info["sample_before"] and info["sample_after"]:
                    print("     sample-before:", info["sample_before"])
                    print("     sample-after :", info["sample_after"])
                print(f"     sha256: {info['sha256'][:16]}...")
        except Exception as e:
            bad += 1
            print(f"[ERROR] {path}: {e}", file=sys.stderr)
    print(f"\nDone. success={ok} failed={bad}")
    return 1 if bad else 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
