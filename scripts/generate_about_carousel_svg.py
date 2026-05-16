#!/usr/bin/env python3
"""Emit assets/about/about-carousel.svg — 3-line beats, clip typing, hold, wipe, loop."""
from __future__ import annotations

W, H = 1100, 138
TYPE = 0.2  # clip expand per line (seconds) — three lines in quick succession
GAP = 0.03  # tiny gap between line clips
HOLD = 6.2  # pause after 3rd line so the beat can be read
WIPE = 0.2  # fade slide out
BETWEEN = 0.08  # gap after wipe before next slide typing

slides = [
    [
        "› who: student dev · practical web · clean UX",
        "› web: JavaScript · React · Node · HTML/CSS",
        "› data: Postgres · Mongo · SQL + NoSQL",
    ],
    [
        "› langs: Kotlin · TypeScript · Python · Java",
        "› local AI: LM Studio + OpenCLAW + Cursor",
        "› work: small deliverables you can ship",
    ],
    [
        "› ship: maintainability over cleverness",
        "› feel: DX + performance from day one",
        "› sandbox: VMs for isolated experiments",
    ],
    [
        "› beyond: Stream Deck + HID batteries",
        "› polish: UI themes + Linux/Windows tuning",
        "› LLMs: local tinkering with LM Studio",
    ],
    [
        "› fun: print(), pray(), more coffee",
        "› lore: one tweak → whole desktop saga",
        "› muscle: openclaw + lmstudio on repeat",
    ],
]

ys = [40, 78, 116]
CLIP_H = 32
CLIP_X = 16
CLIP_W = W - 32


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def sec(x: float) -> str:
    return f"{x:.3f}s"


lines_out: list[str] = []
lines_out.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
    f'aria-label="About carousel">'
)
lines_out.append("  <title>About — three lines per beat</title>")
lines_out.append('  <rect width="100%" height="100%" fill="transparent"/>')
lines_out.append(
    '  <defs><style type="text/css"><![CDATA['
    ".ln{font:19px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#58A6FF;}"
    "]]></style></defs>"
)

# Track last event id for begin= chain
last: str | None = None

for si, texts in enumerate(slides):
    gid = f"g{si}"
    vis0 = "1" if si == 0 else "0"
    lines_out.append(f'  <g id="{gid}" opacity="{vis0}">')

    # Fade this slide in when it becomes active (slides after 0)
    if si > 0:
        prev_wipe = f"wipe{si - 1}"
        lines_out.append(
            f'    <animate id="show{si}" attributeName="opacity" from="0" to="1" '
            f'dur="{sec(0.02)}" begin="{prev_wipe}.end+{sec(BETWEEN)}" fill="freeze"/>'
        )

    for li, (txt, y) in enumerate(zip(texts, ys)):
        cid = f"cp{si}_{li}"
        rid = f"r{si}_{li}"
        aid = f"type{si}_{li}"
        y0 = y - 24
        lines_out.append(f'    <clipPath id="{cid}">')
        lines_out.append(
            f'      <rect id="{rid}" x="{CLIP_X}" y="{y0}" width="0" height="{CLIP_H}">'
        )
        if last is None:
            begin = f"0s; cycl.end+{sec(BETWEEN)}"
        else:
            begin = f"{last}.end+{sec(GAP if li > 0 else BETWEEN)}"
        lines_out.append(
            f'        <animate id="{aid}" attributeName="width" from="0" to="{CLIP_W}" '
            f'dur="{sec(TYPE)}" begin="{begin}" fill="freeze"/>'
        )
        lines_out.append("      </rect>")
        lines_out.append("    </clipPath>")
        lines_out.append(
            f'    <text class="ln" x="{CLIP_X}" y="{y}" clip-path="url(#{cid})">{esc(txt)}</text>'
        )
        last = aid

    hold_id = f"hold{si}"
    lines_out.append('    <rect width="0" height="0" opacity="0" pointer-events="none">')
    lines_out.append(
        f'      <animate id="{hold_id}" attributeName="x" from="0" to="0" '
        f'dur="{sec(HOLD)}" begin="{last}.end" fill="freeze"/>'
    )
    lines_out.append("    </rect>")

    wipe_id = f"wipe{si}"
    lines_out.append(
        f'    <animate id="{wipe_id}" attributeName="opacity" from="1" to="0" '
        f'dur="{sec(WIPE)}" begin="{hold_id}.end" fill="freeze"/>'
    )
    last = wipe_id
    lines_out.append("  </g>")

# Cycle marker after last wipe
lines_out.append('  <rect width="0" height="0" opacity="0" pointer-events="none">')
lines_out.append(
    f'    <animate id="cycl" attributeName="x" from="0" to="0" dur="{sec(0.02)}" '
    f'begin="{last}.end" fill="freeze"/>'
)
lines_out.append("  </rect>")

# Reset clip widths + restore group opacities for next loop
for si in range(len(slides)):
    gid = f"g{si}"
    vis = "1" if si == 0 else "0"
    for li in range(3):
        rid = f"r{si}_{li}"
        lines_out.append(
            f'  <set href="#{rid}" xlink:href="#{rid}" attributeName="width" to="0" '
            f'begin="cycl.end" fill="freeze"/>'
        )
    lines_out.append(
        f'  <set href="#{gid}" xlink:href="#{gid}" attributeName="opacity" to="{vis}" '
        f'begin="cycl.end" fill="freeze"/>'
    )

lines_out.append("</svg>")
out = "\n".join(lines_out) + "\n"

path = "assets/about/about-carousel.svg"
import os

os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write(out)
print("Wrote", path, "bytes", len(out))
