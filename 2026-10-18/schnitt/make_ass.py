def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Inter Display ExtraBold,108,&H00FFFFFF,&H00FFFFFF,&H70000000,&H00000000,0,0,0,0,100,100,-1.5,0,1,7,0,5,40,40,0,1
Style: Num,Inter Display Black,200,&H00FFFFFF,&H00FFFFFF,&H80000000,&H00000000,0,0,0,0,100,100,-4,0,1,8,0,5,40,40,0,1
Style: Small,Inter Display Bold,74,&H00FFFFFF,&H00FFFFFF,&H70000000,&H00000000,0,0,0,0,100,100,-0.5,0,1,6,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
POP = r"\fad(80,60)\fscx86\fscy86\t(0,170,0.6,\fscx100\fscy100)\blur8\t(0,170,\blur0)"
HALO = r"\blur12"
ev=[]
if __name__ == "__main__":
    def line(t0,t1,style,x,y,text,pop=True,extra=""):
        anim = POP if pop else r"\fad(0,60)"
        # two layers: soft dark halo (outline only) below, crisp text above
        ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\an5\\pos({x},{y}){anim}{HALO}\\1a&HFF&{extra}}}{text}")
        ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\an5\\pos({x},{y}){anim}\\bord0{extra}}}{text}")

    # Hook
    line(0.00,1.50,"Hook",540,340,"Das ist kein Video.",pop=False)
    line(1.50,3.00,"Hook",540,340,"Das ist eine Website.")
    line(3.00,4.35,"Hook",540,1330,"Ich hab sie gebaut.")
    # Process
    line(5.50,6.50,"Hook",540,1380,"Ideen sammeln.")
    line(6.50,8.00,"Hook",540,1380,"Code schreiben.")
    line(8.00,9.00,"Hook",540,1380,"Stunden später …")
    # Montage numbers
    for i in range(12):
        t0=9.0+i
        line(t0,t0+1.0,"Num",540,360,f"{i+1:02d}",pop=(i==0) or True)
    # End
    line(21.05,24.50,"Hook",540,1240,"Welche Nummer\\Nist deine?")
    line(21.75,24.50,"Small",540,1435,"Folg mir für Teil 2.")
    open("text.ass","w").write(HEAD+"\n".join(ev)+"\n")
    print(len(ev),"events")
