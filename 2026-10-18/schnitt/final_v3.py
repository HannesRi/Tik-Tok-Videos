import subprocess
FPS = 30; BEAT = 60 / 130
def b(k): return round(k * BEAT * FPS) / FPS
END = b(29)

def flash(label, t0, alpha, d):
    return (f"color=c=white:s=1080x1920:r=30:d={d},format=rgba,colorchannelmixer=aa={alpha},"
            f"fade=t=out:st=0:d={d}:alpha=1,setpts=PTS+{t0:.4f}/TB[{label}]")

def render(part, top_until, bottom_windows):
    bw = "+".join(f"between(t,{a:.4f},{c:.4f})" for a, c in bottom_windows)
    fl = [("f1", b(4), 0.55, 0.12), ("f2", b(15), 0.3, 0.1), ("f3", b(21), 0.3, 0.1)]
    fc = ["[1]format=rgba[gt]", "[2]format=rgba[gb]",
          f"[0][gt]overlay=enable='lt(t,{top_until:.4f})':shortest=1[v1]",
          f"[v1][gb]overlay=enable='{bw}':shortest=1[v2]"]
    fc += [flash(*f) for f in fl]
    last = "v2"
    for i, f in enumerate(fl):
        fc.append(f"[{last}][{f[0]}]overlay=eof_action=pass[w{i}]"); last = f"w{i}"
    fc.append(f"[{last}]subtitles=text_{part}.ass:fontsdir=/usr/share/fonts/opentype/inter,format=yuv420p[v]")
    n = round(END * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", f"cut_{part}.mp4", "-loop", "1", "-i", "grad_screen.png",
           "-loop", "1", "-i", "grad_bottom.png", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
           "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "3:a", "-frames:v", str(n), "-t", f"{END:.4f}",
           "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-profile:v", "high", "-level", "4.2",
           "-maxrate", "25M", "-bufsize", "50M", "-pix_fmt", "yuv420p", "-r", "30", "-g", "30",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", f"../out/{part}.mp4"]
    r = subprocess.run(cmd, capture_output=True, text=True); print(part, r.returncode, r.stderr[-500:])

render("teil1", top_until=0.0, bottom_windows=[(0, b(9)), (b(26), END + 1)])
render("teil2", top_until=b(7), bottom_windows=[(b(7), b(9)), (b(26), END + 1)])
