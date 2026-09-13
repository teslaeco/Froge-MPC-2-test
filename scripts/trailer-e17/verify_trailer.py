"""Verify the delivered movie, then make an evidence contact sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess,json

p=Path(__file__).resolve().parent
f=p/'JULIA-teaser-15s-EN-PL.mp4'
meta=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-show_format','-of','json',str(f)]))
video=next(s for s in meta['streams']if s['codec_type']=='video')
audio=next(s for s in meta['streams']if s['codec_type']=='audio')
assert int(video['nb_frames'])==450
assert abs(float(video['duration'])-15)<.001
assert abs(float(audio['duration'])-15)<.025
assert (video['width'],video['height'])==(720,1280)
r=subprocess.run(['ffmpeg','-nostdin','-v','error','-threads','2','-i',str(f),'-f','null','-'],capture_output=True,text=True)
assert r.returncode==0 and not r.stderr,r.stderr
out=Image.new('RGB',(1200,424),'#0d121a');d=ImageDraw.Draw(out)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
for i,t in enumerate([.7,2.9,4.2,8.3,10.7,12.5]):
    q=p/f'final-frame-{i}.jpg'
    subprocess.run(['ffmpeg','-nostdin','-v','error','-threads','2','-ss',str(t),'-i',str(f),'-frames:v','1','-vf','scale=200:356','-y',str(q)],check=True)
    out.paste(Image.open(q),(i*200,28));d.text((i*200+8,6),f'{t:.1f} s',fill='white',font=font)
d.text((15,397),'15 s · Montaż klipów + render królowej · Narracja EN / napisy PL · Zwiastun koncepcyjny',fill='#c8d7e3',font=font)
out.save(p/'JULIA-teaser-contact.jpg')
v=json.loads((p/'verification.json').read_text())
v.update(full_decode_errors=[],decoded_video_frames=450,video_duration_seconds=float(video['duration']),audio_duration_seconds=float(audio['duration']))
(p/'verification.json').write_text(json.dumps(v,indent=2,ensure_ascii=False))
print('Verified 450 video frames, 15.0 seconds video/audio, complete clean decode.')
