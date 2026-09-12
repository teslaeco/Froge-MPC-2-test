"""Reproducible 15-second edit of user-supplied footage. No generative-video claims."""
from pathlib import Path
import subprocess, json, hashlib, wave, argparse
import numpy as np

ROOT = Path(__file__).resolve().parent
UPLOAD = ROOT.parent / 'upload'
SRC = [UPLOAD / 'user-63blo9IrD4YObhLfFPoz40ei_gen_01k8df9hhzftvr7g42hk0n3t0s_watermarked_md.mp4',
       UPLOAD / 'd5cec0351489d0188772836c306aae01.mp4']
POSTER = UPLOAD / 'file_00000000bcc0822f93205b7413a8e206.png'
parser=argparse.ArgumentParser()
parser.add_argument('--queen-render',type=Path,help='Optional verified render of an actual Queen Neptune mesh')
opts=parser.parse_args()
QUEEN=opts.queen_render.resolve() if opts.queen_render else None
if QUEEN:
    assert QUEEN.is_file(), QUEEN
W,H,FPS,DURATION = 720,1280,30,15

def run(args):
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-threads','2',*map(str,args)],check=True)

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(path)]))

# Full source frame remains visible. Blurred borders adapt different aspect ratios;
# the original Sora/source watermarks are never cropped out or covered by branding.
def normalize(src,start,duration,out,poster=False,title=False):
    inputs = ['-loop','1','-i',src] if poster else ['-ss',start,'-i',src]
    graph = (f'[0:v]fps={FPS},split=2[bg][fg];'
             f'[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2,eq=brightness=-0.22[base];'
             f'[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[sharp];'
             f'[base][sharp]overlay=(W-w)/2:(H-h)/2,setsar=1')
    if title:
        graph += (",gblur=sigma=14,drawbox=x=0:y=0:w=iw:h=ih:color=black@0.63:t=fill"
                  ",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='CONCEPT TEASER':fontsize=22:fontcolor=0xbad8df:x=(w-tw)/2:y=425"
                  ",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf:text='JULIA':fontsize=112:fontcolor=0xf6e8c6:x=(w-tw)/2:y=495"
                  ",drawbox=x=150:y=638:w=420:h=2:color=0xbbae84:t=fill"
                  ",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='8 COSMIC KEYS':fontsize=34:fontcolor=white:x=(w-tw)/2:y=676"
                  ",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='ONE UNIVERSE. ONE CHANCE.':fontsize=22:fontcolor=0xbad8df:x=(w-tw)/2:y=752"
                  ",fade=t=out:st=3.2:d=0.6")
    else:
        graph += ',eq=saturation=1.05:contrast=1.025'
    graph += '[v]'
    run([*inputs,'-filter_complex_threads','2','-filter_complex',graph,'-map','[v]',
         '-t',duration,'-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart','-y',out])

shots = [
    {'name':'meteor','source':0,'start':0.0,'duration':2.2},
    {'name':'girls','source':0,'start':3.5,'duration':1.6},
    {'name':'queen_model' if QUEEN else 'queen_poster','source':'queen' if QUEEN else 'poster','start':0,'duration':1.6},
    {'name':'slingshot','source':1,'start':0.25,'duration':4.6},
    {'name':'cosmic_cube','source':1,'start':5.0,'duration':1.2},
    {'name':'title','source':'poster','start':0,'duration':3.8},
]
for i,s in enumerate(shots):
    src=QUEEN if s['source']=='queen' else POSTER if s['source']=='poster' else SRC[s['source']]
    out=ROOT/f"shot-{i}-queen-{hashlib.sha256(src.read_bytes()).hexdigest()[:10]}.mp4" if s['source']=='queen' else ROOT/f'shot-{i}.mp4'
    try:
        valid=out.exists() and abs(float(probe(out)['format']['duration'])-s['duration'])<.05
    except (KeyError,subprocess.CalledProcessError):
        valid=False
    if not valid:
        normalize(src,s['start'],s['duration'],out,poster=s['source'] in ('poster','queen'),title=s['name']=='title')
    shot_probe=probe(out)
    assert abs(float(shot_probe['format']['duration'])-s['duration'])<.05, (out,shot_probe)
    s['output']=out.name
    print('shot',i,'ready',flush=True)
(ROOT/'concat.txt').write_text(''.join(f"file '{s['output']}'\n" for s in shots))
run(['-f','concat','-safe','0','-i',ROOT/'concat.txt','-c','copy','-y',ROOT/'picture.mp4'])

# Synthetic original score: filtered-noise risers, low percussion, tonal space bed.
# No third-party music and no voice cloning. English narration uses local Flite RMS.
sr=48000;n=int(sr*DURATION);t=np.arange(n)/sr;rng=np.random.default_rng(17)
score=np.zeros(n,np.float64)
for freq,amp in [(55,.065),(82.4069,.025),(110,.017),(164.8138,.012)]:
    score+=amp*np.sin(2*np.pi*freq*t)*(0.65+0.35*np.sin(2*np.pi*.13*t)**2)
noise=rng.standard_normal(n)
smooth=np.convolve(noise,np.ones(25)/25,mode='same')
for at,power in [(0.05,.24),(2.2,.28),(3.8,.25),(5.4,.48),(10,.38),(11.2,.45)]:
    dt=t-at;mask=(dt>=0)&(dt<1.4);x=dt[mask]
    score[mask]+=power*np.sin(2*np.pi*(48*x+17*(1-np.exp(-12*x))))*np.exp(-4.5*x)
    score[mask]+=.11*power*noise[mask]*np.exp(-30*x)
for start,end in [(0,2.2),(4.6,5.4),(8.7,10),(10.5,11.2)]:
    mask=(t>=start)&(t<end);u=(t[mask]-start)/(end-start)
    score[mask]+=.28*smooth[mask]*u**1.7
    score[mask]+=.018*np.sin(2*np.pi*(180*(t[mask]-start)+220*(t[mask]-start)**2))*u
score*=np.minimum(1,t/.12)*np.minimum(1,np.maximum(0,(15-t)/.7))

lines=[(.3,'Eight keys.'),(2.7,'One universe.'),(7.8,'Launch beyond the edge of our world.'),(12.0,'Julia.')]
voice=np.zeros(n,np.float64)
for i,(start,txt) in enumerate(lines):
    textfile=ROOT/f'voice-{i}.txt';textfile.write_text(txt)
    wav=ROOT/f'voice-{i}.wav'
    run(['-f','lavfi','-i',f'flite=textfile={textfile}:voice=rms','-af','highpass=f=100,lowpass=f=6500,atempo=0.92','-ar',sr,'-ac','1','-y',wav])
    with wave.open(str(wav),'rb') as f: samples=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(float)/32768
    samples*=.49/max(.01,np.max(np.abs(samples)))
    startidx=int(start*sr);endidx=min(n,startidx+len(samples));voice[startidx:endidx]+=samples[:endidx-startidx]
    # A restrained echo adds depth without hiding the low-fidelity synthesized voice.
    for delay,gain in [(.09,.11),(.19,.045)]:
        a=startidx+int(delay*sr);b=min(n,a+len(samples));voice[a:b]+=gain*samples[:b-a]
    mask=(t>=start-.12)&(t<=start+len(samples)/sr+.2);score[mask]*=.35
    print('voice',i,'duration',len(samples)/sr,flush=True)

mix=np.tanh((score+voice)*1.2)*.89
stereo=np.column_stack([mix,np.tanh((np.roll(score,170)+voice)*1.2)*.89])
with wave.open(str(ROOT/'soundtrack-en.wav'),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(stereo,-1,1)*32767).astype('<i2').tobytes())

srt='''1
00:00:00,300 --> 00:00:01,950
Osiem kluczy.

2
00:00:02,700 --> 00:00:04,350
Jeden wszechświat.

3
00:00:07,800 --> 00:00:11,350
Wyrusz poza granice naszego świata.

4
00:00:12,000 --> 00:00:13,200
Julia.
'''
(ROOT/'JULIA-teaser-PL.srt').write_text(srt)
style='FontName=DejaVu Sans,FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00100804,BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=24'
run(['-i',ROOT/'picture.mp4','-i',ROOT/'soundtrack-en.wav','-vf',f"subtitles={ROOT/'JULIA-teaser-PL.srt'}:force_style='{style}'",'-map','0:v','-map','1:a','-t',15,'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','192k','-movflags','+faststart','-y',ROOT/'JULIA-teaser-15s-EN-PL.mp4'])
final=probe(ROOT/'JULIA-teaser-15s-EN-PL.mp4')
assert float(final['format']['duration'])<=15.05
assert {s['codec_type']for s in final['streams']}=={'audio','video'}
assert int(next(s for s in final['streams']if s['codec_type']=='video')['nb_frames'])==450
report={'duration_seconds':float(final['format']['duration']),'resolution':[W,H],'fps':FPS,'shots':shots,'voice':'Local Flite RMS synthetic English narration','subtitles':'Polish, burned in and SRT','music':'Procedural original synthesized score','source_audio_used':False,'source_watermarks':'Retained within full source frame','new_queen_mesh_still_render_included':bool(QUEEN),'main_E17_character_mesh_included':False,'capsule_boarding_depicted':False,'mountain_scale_verified':False,'video_generation_performed':False,'sources':[{'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [*SRC,POSTER,*([QUEEN]if QUEEN else [])]],'output_sha256':hashlib.sha256((ROOT/'JULIA-teaser-15s-EN-PL.mp4').read_bytes()).hexdigest()}
if QUEEN and (QUEEN.parent/'render-verification.json').is_file():
    report['queen_render_verification']=json.loads((QUEEN.parent/'render-verification.json').read_text())
(ROOT/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('COMPLETE',json.dumps({'duration':report['duration_seconds'],'output':str(ROOT/'JULIA-teaser-15s-EN-PL.mp4')}),flush=True)
