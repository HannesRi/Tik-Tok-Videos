import subprocess
from make_ass_v4 import g, END
for part in ("teil1", "teil2"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"concat4_{part}.txt", "-c", "copy", f"cut4_{part}.mp4"], check=True)
    n = round(END * 30)
    fc = (f"[1]format=rgba[ge];[0][ge]overlay=enable='gte(t,{g(30):.4f})':shortest=1,"
          f"subtitles=text4_{part}.ass:fontsdir=/usr/share/fonts/opentype/inter,"
          f"noise=c0s=4:c0f=t+u,format=yuv420p[v]")
    common = ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-profile:v", "high", "-level", "4.2",
              "-maxrate", "30M", "-bufsize", "60M", "-pix_fmt", "yuv420p", "-r", "30", "-g", "30",
              "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart"]
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"cut4_{part}.mp4", "-loop", "1", "-i", "grad_end.png",
                        "-i", "phonk.wav", "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
                        "-frames:v", str(n), "-t", f"{END:.4f}", *common, "-c:a", "aac", "-b:a", "256k",
                        f"../out/{part}_mit_sound.mp4"], capture_output=True, text=True)
    print(part, "sound", r.returncode, r.stderr[-300:])
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"../out/{part}_mit_sound.mp4", "-f", "lavfi",
                        "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "128k", "-t", f"{END:.4f}", "-movflags", "+faststart",
                        f"../out/{part}_ohne_sound.mp4"], capture_output=True, text=True)
    print(part, "silent", r.returncode, r.stderr[-300:])
