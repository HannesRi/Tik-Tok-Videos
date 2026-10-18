from make_ass import HEAD, POP, HALO, ts
ev = []
def line(t0, t1, style, x, y, text, pop=True, an=5):
    anim = POP if pop else r"\fad(0,0)"
    ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\an{an}\\pos({x},{y}){anim}{HALO}\\1a&HFF&}}{text}")
    ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\an{an}\\pos({x},{y}){anim}\\bord0}}{text}")
line(0.00, 1.83, "Hook", 540, 330, "Das ist kein Video.", pop=False)
line(1.83, 4.60, "Hook", 540, 330, "Das sind Websites.")
line(4.60, 7.40, "Hook", 540, 330, "Alle selbst gebaut.")
line(7.40, 9.30, "Hook", 70, 900, "Folg mir\\Nfür Teil 2.", an=1)
open("text_v2.ass", "w").write(HEAD + "\n".join(ev) + "\n")
