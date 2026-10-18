from make_ass import HEAD, POP, HALO, ts
FPS = 30; BEAT = 60 / 130
def b(k): return round(k * BEAT * FPS) / FPS
HEAD3 = HEAD.replace("[Events]", "Style: Label,Inter Display SemiBold,46,&H30FFFFFF,&H00FFFFFF,&H80000000,&H00000000,0,0,0,0,100,100,9,0,1,6,0,5,40,40,0,1\n\n[Events]")

def build(lines, path):
    ev = []
    for t0, t1, style, x, y, text, pop in lines:
        anim = POP if pop else r"\fad(0,0)"
        ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\an5\\pos({x},{y}){anim}{HALO}\\1a&HFF&}}{text}")
        ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\an5\\pos({x},{y}){anim}\\bord0}}{text}")
    open(path, "w").write(HEAD3 + "\n".join(ev) + "\n")

END = b(29)
build([
    (0, b(7), "Label", 540, 1285, "TEIL 1", False),
    (0, b(4), "Hook", 540, 1400, "Das ist kein Video.", False),
    (b(4), b(7), "Hook", 540, 1400, "Das ist eine Website.", True),
    (b(7), b(9), "Hook", 540, 1400, "Gebaut von mir.", True),
    (b(26), END + 0.1, "Hook", 540, 1360, "Teil 2 →", True),
    (b(26) + 0.25, END + 0.1, "Small", 540, 1480, "auf meinem Profil", True),
], "text_teil1.ass")
build([
    (0, b(7), "Label", 540, 235, "TEIL 2", False),
    (0, b(4), "Hook", 540, 350, "Auch kein Video.", False),
    (b(4), b(7), "Hook", 540, 350, "Auch eine Website.", True),
    (b(7), b(9), "Hook", 540, 1400, "Alles selbst gebaut.", True),
    (b(26), END + 0.1, "Hook", 540, 1330, "Welche war\\Ndie beste?", True),
    (b(26) + 0.25, END + 0.1, "Small", 540, 1500, "Folg mir für mehr.", True),
], "text_teil2.ass")
print("b4", b(4), "b7", b(7), "b9", b(9), "b26", b(26), "end", END)
