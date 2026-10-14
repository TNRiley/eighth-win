"""Splice src/payload.json into src/template.html and write ../index.html, then
run the catalog's two finishing steps (Pages wrapper, breadcrumb bar).

    python src/inject.py
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MARK = "__PAYLOAD__"

def workspace_root(start):
    d = os.path.abspath(start)
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, "projects")):
            return d
        d = os.path.dirname(d)
    sys.exit("could not find the workspace root")

def main():
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    payload = open(os.path.join(HERE, "payload.json"), encoding="utf-8").read()
    if tpl.count(MARK) != 1:
        sys.exit("template.html must contain %s exactly once" % MARK)
    out = os.path.join(PROJECT, "index.html")
    open(out, "w", encoding="utf-8", newline="\n").write(tpl.replace(MARK, payload))
    print("index.html %.0f kB" % (os.path.getsize(out) / 1e3))
    tools = os.path.join(workspace_root(HERE), "catalog", "tools")
    for script in ("wrap_for_pages.py", "add_catalog_link.py"):
        subprocess.run([sys.executable, os.path.join(tools, script), out], check=True)

if __name__ == "__main__":
    main()
