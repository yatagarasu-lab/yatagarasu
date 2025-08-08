# ops/apply_changes.py
import os, sys, io, datetime, pathlib, re
import yaml
from jinja2 import Template

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG  = ROOT / "ops" / "desired_changes.yaml"
TEMPL_DIR = ROOT / "ops" / "templates"

def now_str():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

def read_text(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""

def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def render(s, ctx):
    return Template(s).render(**ctx)

def apply_edit(edit, ctx):
    target = ROOT / edit["file"]
    original = read_text(target)
    updated = original

    # 1) insert_end
    if "insert_end" in edit:
      frag = render(edit["insert_end"], ctx)
      if not updated.endswith("\n"):
          updated += "\n"
      updated += frag

    # 2) replace（正規表現）
    for rep in edit.get("replace", []):
      pat = rep["pattern"]
      repl = render(rep["replacement"], ctx)
      updated = re.sub(pat, repl, updated, flags=re.MULTILINE)

    # 3) set_line（1始まり）
    if "set_line" in edit:
      ln = int(edit["set_line"]["line"])
      txt = render(edit["set_line"]["text"], ctx)
      lines = updated.splitlines()
      while len(lines) < ln:
          lines.append("")
      lines[ln-1] = txt
      updated = "\n".join(lines) + ("\n" if original.endswith("\n") else "")

    # 4) from_template（テンプレファイルを末尾に追記）
    if "from_template" in edit:
      tpl_path = TEMPL_DIR / edit["from_template"]
      tpl = read_text(tpl_path)
      frag = Template(tpl).render(**ctx)
      if not updated.endswith("\n"):
          updated += "\n"
      updated += frag

    if updated != original:
        write_text(target, updated)
        print(f"[update] {target}")
        return True

    print(f"[skip]   {target} (no changes)")
    return False

def main():
    if not CFG.exists():
        print("[info] ops/desired_changes.yaml not found, nothing to do.")
        return

    cfg = yaml.safe_load(read_text(CFG)) or {}
    edits = cfg.get("edits", [])
    ctx = {
        "now": now_str(),
    }
    changed = False
    for e in edits:
        changed |= apply_edit(e, ctx)

    if not changed:
        print("[info] No file updated by desired_changes.")
    else:
        print("[info] Changes applied.")

if __name__ == "__main__":
    main()
