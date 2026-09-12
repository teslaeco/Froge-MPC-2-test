from PIL import Image
import numpy as np,json
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
old=np.asarray(Image.open('upload/Screenshot_20260912-131922.png').convert('RGB'),dtype=float)/255
new=np.asarray(Image.open('upload/Screenshot_20260912-170529.png').convert('RGB'),dtype=float)/255
y,x=np.mgrid[340:730:5,300:590:5];x=x.ravel();y=y.ravel();target=old[y,x]
def fun(p):
 s,tx,ty=p;nx=x*s+tx;ny=y*s+ty
 sample=np.stack([map_coordinates(new[:,:,c],[ny,nx],order=1) for c in range(3)],1)
 return (sample-target).ravel()
r=least_squares(fun,[1.4,-190,-173],diff_step=1e-4,max_nfev=100,loss='soft_l1',f_scale=.03)
out={'scale':r.x[0],'translate_x':r.x[1],'translate_y':r.x[2],'fit_rgb_rmse':float(np.sqrt(np.mean(fun(r.x)**2))),'samples':len(x),'source':'same artwork zoomed reference; no invented facial detail'};print(out);open('materials-r13/reference-registration.json','w').write(json.dumps(out,indent=2))
