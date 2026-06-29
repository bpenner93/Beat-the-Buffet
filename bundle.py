#!/usr/bin/env python3
"""Bundle index.html + data.js into ONE self-contained file you can share.
Run after build_data.py whenever the data changes:  python bundle.py
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
data = open(os.path.join(HERE, "data.js"), encoding="utf-8").read()

# Inline data.js in place of the external <script src> so the file works on its own.
bundled = html.replace('<script src="data.js"></script>', "<script>\n" + data + "\n</script>")

out = os.path.join(HERE, "beat-the-buffett.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(bundled)

kb = len(bundled.encode("utf-8")) // 1024
if '<script src="data.js">' in bundled:
    print("WARNING: data.js reference still present — bundling failed.")
else:
    print(f"Wrote beat-the-buffett.html ({kb} KB) — one self-contained file, no data.js needed.")
