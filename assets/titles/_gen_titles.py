#!/usr/bin/env python3
"""Regenerate glitch-*.svg title reels: 32 fast shuffle frames in first 25%% of dur, hold final 75%%; per-char tspans with dim + chroma/skew/blur glitches."""

from __future__ import annotations

def keytimes_shuffle_hold(shuffle_steps: int = 32, shuffle_frac: float = 0.25) -> str:
    # shuffle_steps keyTimes in [0, shuffle_frac), then shuffle_frac, then 1.0 (duplicate final state)
    kt = [round(k / shuffle_steps * shuffle_frac, 8) for k in range(shuffle_steps)]
    kt.append(shuffle_frac)
    kt.append(1.0)
    return ";".join(str(x) for x in kt)


def translate_values(line: int) -> str:
    vals = [f"0,{-i * line}" for i in range(32)]
    t = -32 * line
    vals.extend([f"0,{t}", f"0,{t}"])
    return ";".join(vals)


def dur_seconds(dur: str) -> float:
    return float(dur.removesuffix("s"))


def esc_xml_tspan(ch: str) -> str:
    if ch == "&":
        return "&amp;"
    if ch == "<":
        return "&lt;"
    if ch == ">":
        return "&gt;"
    return ch


def char_stagger_s(row_idx: int, char_idx: int, line: str, dur: str) -> float:
    """Per-char offset in [0, dur) so dips desync across rows and positions."""
    ds = dur_seconds(dur)
    h = row_idx * 59 + char_idx * 31 + sum(ord(c) for c in line) * 3
    return (h % 997) / 997.0 * max(ds * 0.97, 0.01)


def tspan_anim_delay(row_idx: int, char_idx: int, line: str, dur: str, anim_delay: str) -> float:
    """Align char cycle with SMIL reel + per-char stagger."""
    ds = dur_seconds(dur)
    base = dur_seconds(anim_delay)
    return (base + char_stagger_s(row_idx, char_idx, line, dur)) % ds


def tspans_for_line(s: str, row_idx: int, dur: str, anim_delay: str) -> str:
    parts: list[str] = []
    for j, ch in enumerate(s):
        inner = esc_xml_tspan(ch)
        delay = tspan_anim_delay(row_idx, j, s, dur, anim_delay)
        parts.append(f'<tspan class="ch" style="animation-delay:{delay:.3f}s">{inner}</tspan>')
    return "".join(parts)


CALM_CHAR = (
    "opacity:1;"
    "transform:translate(0,0) skewX(0deg) scaleX(1);"
    "filter:none;"
    "text-shadow:0 0 6px rgba(56,189,248,.14),0 0 1px rgba(120,190,255,.28);"
)


def _glitch_shuffle(i: int) -> tuple[dict[str, float | str], dict[str, float | str]]:
    """Peak + tail (motion smear) keyframe payloads for shuffle-phase glitches."""
    peaks = (
        dict(
            op=0.32,
            dx=-5.0,
            skew=-6.0,
            sx=0.91,
            blur=0.95,
            sh=(
                "-6px 0 0 rgba(255,75,130,.58),6px 0 0 rgba(55,220,255,.55),"
                "-12px 0 14px rgba(160,210,255,.42),12px 0 14px rgba(70,195,255,.32),"
                "0 0 10px rgba(230,245,255,.5)"
            ),
        ),
        dict(
            op=0.36,
            dx=5.0,
            skew=5.5,
            sx=1.08,
            blur=0.8,
            sh=(
                "7px 0 0 rgba(255,90,150,.52),-7px 0 0 rgba(50,210,255,.58),"
                "13px 0 12px rgba(100,190,255,.38),-13px 0 12px rgba(180,220,255,.35),"
                "0 0 8px rgba(255,255,255,.45)"
            ),
        ),
        dict(
            op=0.3,
            dx=-3.5,
            skew=7.0,
            sx=0.88,
            blur=1.05,
            sh=(
                "-5px 0 0 rgba(255,120,180,.5),5px 0 0 rgba(40,200,245,.55),"
                "-10px 0 18px rgba(130,200,255,.45),10px 0 18px rgba(60,170,255,.3),"
                "-2px 0 6px rgba(255,255,255,.4)"
            ),
        ),
        dict(
            op=0.35,
            dx=4.0,
            skew=-4.0,
            sx=1.05,
            blur=0.72,
            sh=(
                "-4px 0 0 rgba(255,70,120,.55),4px 0 0 rgba(65,230,255,.52),"
                "-9px 0 10px rgba(200,230,255,.4),9px 0 10px rgba(80,185,255,.35),"
                "0 1px 8px rgba(220,240,255,.42)"
            ),
        ),
    )
    p = peaks[i % len(peaks)]
    tail = dict(
        op=min(float(p["op"]) + 0.22, 0.78),
        dx=-float(p["dx"]) * 0.45,
        skew=-float(p["skew"]) * 0.35,
        sx=float(p["sx"]) + (1.0 - float(p["sx"])) * 0.4,
        blur=max(float(p["blur"]) * 0.42, 0.35),
        sh=(
            "-3px 0 0 rgba(255,100,160,.35),3px 0 0 rgba(80,210,255,.38),"
            "-6px 0 8px rgba(140,200,255,.28),6px 0 8px rgba(90,190,255,.22),"
            "0 0 5px rgba(200,230,255,.32)"
        ),
    )
    return p, tail


def _glitch_hold(i: int) -> tuple[dict[str, float | str], dict[str, float | str]]:
    peaks = (
        dict(
            op=0.38,
            dx=-3.0,
            skew=-3.5,
            sx=0.94,
            blur=0.55,
            sh=(
                "-4px 0 0 rgba(255,95,140,.45),4px 0 0 rgba(70,215,255,.48),"
                "-8px 0 10px rgba(150,210,255,.32),8px 0 10px rgba(85,195,255,.25),"
                "0 0 6px rgba(220,240,255,.38)"
            ),
        ),
        dict(
            op=0.42,
            dx=3.0,
            skew=3.0,
            sx=1.04,
            blur=0.48,
            sh=(
                "4px 0 0 rgba(255,85,130,.42),-4px 0 0 rgba(60,220,255,.45),"
                "8px 0 8px rgba(120,200,255,.28),-8px 0 8px rgba(160,220,255,.26),"
                "0 0 5px rgba(230,245,255,.35)"
            ),
        ),
        dict(
            op=0.4,
            dx=-2.0,
            skew=4.0,
            sx=0.96,
            blur=0.62,
            sh=(
                "-3px 0 0 rgba(255,110,170,.4),3px 0 0 rgba(55,205,250,.44),"
                "-7px 0 12px rgba(170,220,255,.3),7px 0 12px rgba(75,185,255,.24),"
                "0 0 7px rgba(210,235,255,.36)"
            ),
        ),
    )
    p = peaks[i % len(peaks)]
    tail = dict(
        op=min(float(p["op"]) + 0.18, 0.82),
        dx=-float(p["dx"]) * 0.4,
        skew=-float(p["skew"]) * 0.3,
        sx=float(p["sx"]) + (1.0 - float(p["sx"])) * 0.35,
        blur=max(float(p["blur"]) * 0.38, 0.28),
        sh=(
            "-2px 0 0 rgba(255,120,170,.28),2px 0 0 rgba(90,215,255,.32),"
            "-4px 0 6px rgba(150,210,255,.22),4px 0 6px rgba(100,195,255,.18),"
            "0 0 4px rgba(200,230,255,.25)"
        ),
    )
    return p, tail


def _css_glitch(g: dict[str, float | str]) -> str:
    op = round(float(g["op"]), 2)
    dx = round(float(g["dx"]), 2)
    skew = round(float(g["skew"]), 2)
    sx = round(float(g["sx"]), 3)
    blur = round(float(g["blur"]), 2)
    sh = str(g["sh"])
    return (
        f"opacity:{op};"
        f"transform:translate({dx}px,0) skewX({skew}deg) scaleX({sx});"
        f"filter:blur({blur}px);"
        f"text-shadow:{sh};"
    )


def build_char_dim_keyframes() -> str:
    """Sparse glitches: peak (chroma + skew + blur + dim), short tail, then calm."""
    by_t: dict[float, str] = {}
    for i, p in enumerate((0.7, 2.1, 3.8, 5.9, 8.4, 11.2, 14.0, 17.5, 20.8, 23.5)):
        peak, tail = _glitch_shuffle(i)
        t0 = round(p, 2)
        t1 = round(min(p + 0.055, 24.9), 2)
        t2 = round(min(p + 0.15, 24.98), 2)
        by_t[t0] = _css_glitch(peak)
        by_t[t1] = _css_glitch(tail)
        by_t[t2] = CALM_CHAR
    for i, p in enumerate((34, 48, 58, 69, 79, 90)):
        peak, tail = _glitch_hold(i)
        t0 = round(float(p), 2)
        t1 = round(min(p + 0.05, 99.88), 2)
        t2 = round(min(p + 0.13, 99.95), 2)
        by_t[t0] = _css_glitch(peak)
        by_t[t1] = _css_glitch(tail)
        by_t[t2] = CALM_CHAR
    by_t[0.0] = CALM_CHAR
    by_t[100.0] = CALM_CHAR
    return "\n".join(f"        {t}% {{{by_t[t]}}}" for t in sorted(by_t))


def wrap_svg(
    vid: str,
    view_w: int,
    view_h: int,
    title: str,
    aria: str,
    line_h: int,
    y0: int,
    cx: int,
    font_row: str,
    font_final: str,
    junk_lines: list[str],
    final_line: str,
    dur: str,
    anim_delay: str,
) -> str:
    assert len(junk_lines) == 32, len(junk_lines)
    kt = keytimes_shuffle_hold()
    tv = translate_values(line_h)
    ys = [y0 + i * line_h for i in range(33)]
    rows = []
    for i, s in enumerate(junk_lines):
        inner = tspans_for_line(s, i, dur, anim_delay)
        rows.append(
            f'      <text class="row" x="{cx}" y="{ys[i]}" xml:space="preserve">{inner}</text>'
        )
    fin = tspans_for_line(final_line, 32, dur, anim_delay)
    rows.append(f'      <text class="final" x="{cx}" y="{ys[32]}" xml:space="preserve">{fin}</text>')
    body = "\n".join(rows)
    dim_kf = build_char_dim_keyframes()
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {view_h}" width="{view_w}" height="{view_h}" overflow="hidden" role="img" aria-label="{aria}">
  <title>{title}</title>
  <defs>
    <clipPath id="clip-{vid}"><rect x="0" y="0" width="{view_w}" height="{view_h}"/></clipPath>
    <style type="text/css"><![CDATA[
      .row{{{font_row}text-shadow:0 0 6px rgba(56,189,248,.14),0 0 1px rgba(120,190,255,.28);}}
      .final{{{font_final}text-shadow:0 0 6px rgba(56,189,248,.14),0 0 1px rgba(120,190,255,.28);}}
      .row tspan.ch, .final tspan.ch {{
        transform-box: fill-box;
        transform-origin: 50% 50%;
        animation: charDim-{vid} {dur} linear infinite;
      }}
      #slotwrap-{vid}{{
        animation: jiggle-{vid} {dur} ease-in-out infinite;
        animation-delay: {anim_delay};
        transform-origin: {cx}px {view_h // 2}px;
      }}
      @keyframes jiggle-{vid}{{
        0%, 26%, 100% {{ transform: translate(0,0); }}
        26.02% {{ transform: translate(-2px, 0); }}
        26.05% {{ transform: translate(3px, 0); }}
        26.08% {{ transform: translate(0, 0); }}
        42%, 42.02% {{ transform: translate(-1px, 0); }}
        42.04% {{ transform: translate(0, 0); }}
        54%, 54.02% {{ transform: translate(2px, 0); }}
        54.04% {{ transform: translate(0, 0); }}
        66%, 66.02% {{ transform: translate(-2px, 0); }}
        66.04% {{ transform: translate(0, 0); }}
        77%, 77.02% {{ transform: skewX(1deg); }}
        77.04% {{ transform: skewX(0); }}
        88%, 88.02% {{ transform: translate(1px, 0); }}
        88.04% {{ transform: translate(0, 0); }}
      }}
      @keyframes charDim-{vid}{{
{dim_kf}
      }}
    ]]></style>
  </defs>
  <g clip-path="url(#clip-{vid})">
    <g id="slotwrap-{vid}">
      <g>
        <animateTransform attributeName="transform" type="translate" additive="replace" calcMode="discrete"
          values="{tv}"
          keyTimes="{kt}"
          dur="{dur}" begin="{anim_delay}" repeatCount="indefinite"/>
{body}
      </g>
    </g>
  </g>
</svg>
'''




# --- About (5 chars) ---
about_junk = [
    "?????", "#####", "@#$%+", "~!@#$", "`~!@#", "[?]!@", "\\|/_+", "???@@",
    "@@###", "#?@?#", "%Ab??", "@b???", "4b???", "4b0??", "@b0u+", "#b0u+",
    "@b0u7", "4b0u7", "4b0u+", "Ab0??", "Ab0u+", "Ab0u7", "Ab0ut", "Ab0u7",
    "Abo?t", "Abo7t", "Ab|ut", "Ab0nt", "Abou+", "Abou7", "Abo7t", "Ab0ut",
]

# --- Contact (7) ---
contact_junk = [
    "%%%%%%%", "?@#$%+*", "C0nt4c?", "c0NT4CT", "C0nt4ct", "C0ntact", "Cont4ct",
    "Cont4c7", "Conta7t", "Contac7", "C0ntact", "Cont4ct", "Contac7", "C0nt4ct",
    "C0nt4c?", "Contact",     "C0ntact", "Cont4ct", "Contac7", "C0nt4ct", "Contact",
    "Cont4ct", "C0ntact", "Cont4ct", "Contac7", "C0nt4ct", "Contact", "Cont4ct",
    "C0ntact", "Cont4ct", "Contac7", "C0nt4ct",
]

# --- GitHub Pulse (12) ---
pulse_junk = [
    "############", "G1tH*b Puls?", "G#tHub P*ls?", "G1tHub Puls3", "GitH*b Puls?",
    "GitHub P*lse", "G#tHub Pulse", "GitH*b Pulse", "G1tHub Puls?", "GitHub Puls3",
    "GitHub P*lse", "G#tHub Pulse", "GitH*b Pulse", "GitHub Puls?", "G1tHub Pulse",
    "GitHub P*lse", "G#tHub Pulse", "GitH*b Pulse", "GitHub Puls3", "GitHub Pulse",
    "G1tHub Puls?", "GitH*b Pulse", "GitHub P*lse", "G#tHub Pulse", "G1tHub Pulse",
    "GitHub Puls3", "GitH*b Pulse", "GitHub Puls?", "G#tHub Pulse", "GitHub P*lse",
    "G1tHub Pulse", "GitHub Puls3",
]

# --- Stack and tools (15) ---
stack_junk = [
    "###############", "St4ck 4nd t00ls", "St@ck #nd t00ls", "St4ck @nd t00ls",
    "Stack #nd t00ls", "Stack 4nd t00ls", "Stack @nd t00ls", "Stack and t00ls",
    "Stack @nd t01ls", "St4ck and t00ls", "Stack 4nd t0ols", "Stack and t01ls",
    "Stack and t0ols", "St4ck and tools", "Stack @nd tools", "Stack and t00ls",
    "Stack and tool5", "St4ck and tools", "Stack @nd tools", "Stack and t00ls",
    "Stack and tool5", "St4ck and tools", "Stack and tools", "St4ck and tools",
    "Stack @nd tools", "Stack and t00ls", "Stack and tools", "St4ck and tools",
    "Stack and tools", "Stack @nd tools", "Stack and t00ls", "Stack and tools",
]

# --- Hey (15) ---
hey_junk = [
    "###############", "!@#$%^*()_+[]|", "~~~###@@@???%%%", "???|||###@@@???",
    "H?y, !m T3lluz", "H@y, !m T3||uz", "H3y, !' T3||uz", "H@y, !' T311uz",
    "H@y, !' T3l1uz", "H@y, !' T3lluz", "H@y, I'm T3lluz", "H3y, I'm T3lluz",
    "Hey, I'm T311uz", "Hey, I'm T3l1uz", "Hey, I'm T3lluz", "Hey, !'m T3lluz",
    "Hey, I'm T3||uz", "Hey, I'm T3lluz", "H3y, I'm T3lluz", "Hey, I'm T3l1uz",
    "Hey, I'm T3lluz", "Hey, I'm T3||uz", "Hey, I'm T3lluz", "H3y, I'm T3lluz",
    "Hey, I'm T3l1uz", "Hey, I'm T3lluz", "Hey, !'m T3lluz", "Hey, I'm T3||uz",
    "Hey, I'm T3lluz", "H3y, I'm T3lluz", "Hey, I'm T3l1uz", "Hey, I'm T3lluz",
]

assert len(about_junk) == 32
assert len(contact_junk) == 32
assert len(pulse_junk) == 32
assert len(stack_junk) == 32
assert len(hey_junk) == 32

FONT_ROW_ABOUT = "font:800 26px ui-monospace,system-ui,monospace;fill:#c8e4ff;letter-spacing:.14em;text-anchor:middle;"
FONT_FIN_ABOUT = "font:800 26px ui-sans-serif,system-ui,sans-serif;fill:#c8e4ff;letter-spacing:.12em;text-anchor:middle;"

FONT_ROW_24 = "font:800 24px ui-monospace,system-ui,monospace;fill:#c8e4ff;letter-spacing:.09em;text-anchor:middle;"
FONT_FIN_24 = "font:800 24px ui-sans-serif,system-ui,sans-serif;fill:#c8e4ff;letter-spacing:.1em;text-anchor:middle;"

FONT_ROW_HEY = "font:800 22px ui-monospace,system-ui,monospace;fill:#c8e4ff;letter-spacing:.08em;text-anchor:middle;"
FONT_FIN_HEY = "font:800 22px ui-sans-serif,system-ui,sans-serif;fill:#c8e4ff;letter-spacing:.1em;text-anchor:middle;"

out_dir = __file__.rsplit("/", 1)[0]

def write(name, content):
    path = f"{out_dir}/{name}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", path)

write(
    "glitch-about.svg",
    wrap_svg(
        "about",
        200,
        52,
        "About",
        "About",
        46,
        36,
        100,
        FONT_ROW_ABOUT,
        FONT_FIN_ABOUT,
        about_junk,
        "About",
        "20.41s",
        "0.27s",
    ),
)

write(
    "glitch-contact.svg",
    wrap_svg(
        "contact",
        220,
        52,
        "Contact",
        "Contact",
        46,
        36,
        110,
        FONT_ROW_ABOUT,
        FONT_FIN_ABOUT,
        contact_junk,
        "Contact",
        "19.13s",
        "1.82s",
    ),
)

write(
    "glitch-pulse.svg",
    wrap_svg(
        "pulse",
        320,
        52,
        "GitHub Pulse",
        "GitHub Pulse",
        46,
        36,
        160,
        FONT_ROW_24,
        FONT_FIN_24,
        pulse_junk,
        "GitHub Pulse",
        "22.67s",
        "0.93s",
    ),
)

write(
    "glitch-stack.svg",
    wrap_svg(
        "stack",
        380,
        52,
        "Stack and tools",
        "Stack and tools",
        46,
        36,
        190,
        FONT_ROW_24,
        FONT_FIN_24,
        stack_junk,
        "Stack and tools",
        "21.29s",
        "2.14s",
    ),
)

write(
    "glitch-hey.svg",
    wrap_svg(
        "hey",
        460,
        54,
        "Hey, I'm T3lluz",
        "Hey, I'm T3lluz",
        64,
        38,
        230,
        FONT_ROW_HEY,
        FONT_FIN_HEY,
        hey_junk,
        "Hey, I'm T3lluz",
        "18.76s",
        "1.05s",
    ),
)

print("done")
