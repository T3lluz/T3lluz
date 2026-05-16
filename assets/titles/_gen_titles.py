#!/usr/bin/env python3
"""Regenerate glitch-*.svg title reels: 32 fast shuffle frames in first 25%% of dur, hold final 75%%; sparse per-char dim via tspans + CSS."""

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


def build_char_dim_keyframes() -> str:
    """Few narrow opacity dips (shuffle busier than hold); paired with per-tspan animation-delay."""
    events: list[tuple[float, float]] = []
    for p in (0.7, 2.1, 3.8, 5.9, 8.4, 11.2, 14.0, 17.5, 20.8, 23.5):
        events.append((p, 0.34))
        events.append((min(p + 0.16, 24.95), 1.0))
    for p in (34, 48, 58, 69, 79, 90):
        events.append((p, 0.4))
        events.append((min(p + 0.14, 99.92), 1.0))
    events.append((0.0, 1.0))
    events.append((100.0, 1.0))
    by_t: dict[float, float] = {}
    for t, op in events:
        t = round(t, 2)
        by_t[t] = op
    return "\n".join(
        f"        {t}% {{ opacity: {by_t[t]}; }}" for t in sorted(by_t)
    )


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
