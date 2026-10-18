from make_ass import ts
FPS = 30; BEAT = 60 / 130
def g(k): return round(k * BEAT * FPS) / FPS
END = g(33)
HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display Medium,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0.3,0,1,0,0,5,40,40,0,1
Style: Lab,Inter Display Medium,28,&H55FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,9,0,1,0,0,5,40,40,0,1
Style: Sub,Inter Display Regular,40,&H45FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0.3,0,1,0,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def build(lines, path):
    ev = []
    for t0, t1, style, x, y, text in lines:
        anim = f"\\fad(260,220)\\move({x},{y + 14},{x},{y},0,420)"
        # soft, barely visible shadow layer for legibility on bright backgrounds
        ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{{anim}\\1a&HFF&\\3c&H000000&\\3a&HB0&\\bord4\\blur10}}{text}")
        ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{{anim}}}{text}")
    open(path, "w").write(HEAD + "\n".join(ev) + "\n")

build([
    (0.30, g(8), "Lab", 540, 292, "TEIL 1"),
    (0.30, g(8), "Cap", 540, 356, "Ich baue Websites wie diese."),
    (g(30) + 0.15, END + 0.2, "Cap", 540, 1400, "Teil 2 auf meinem Profil."),
], "text4_teil1.ass")
build([
    (0.30, g(8), "Lab", 540, 292, "TEIL 2"),
    (0.30, g(8), "Cap", 540, 356, "Ich baue Websites wie diese."),
    (g(30) + 0.15, END + 0.2, "Cap", 540, 1380, "Welche war die beste?"),
    (g(30) + 0.35, END + 0.2, "Sub", 540, 1452, "Folg mir für mehr."),
], "text4_teil2.ass")
print("hook end", g(8), "end shot", g(30), "END", END)
