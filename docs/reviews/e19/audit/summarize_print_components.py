"""Connected-shell inventory for arrays exported by inspect_print_components.py."""
import scipy,numpy as np,json
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'print';data=np.load(root/'print-geometry.npz');v=data['vertices'];f=data['faces'];edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);g=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(v),len(v))).tocsr();n,labels=connected_components(g,directed=False);np.save(root/'component-labels.npy',labels)
rows=[]
for c in range(n):
 ix=np.where(labels==c)[0];ff=f[labels[f[:,0]]==c];vv=v[ix];a,b,d=v[ff[:,0]],v[ff[:,1]],v[ff[:,2]];vol=np.einsum('ij,ij->i',a,np.cross(b,d)).sum()/6
 rows.append(dict(component=c,triangles=len(ff),vertices=len(ix),min_mm=vv.min(0).tolist(),max_mm=vv.max(0).tolist(),signed_volume_mm3=float(vol)))
rows.sort(key=lambda r:r['triangles'],reverse=True);(root/'print-components.json').write_text(json.dumps(rows,indent=2));print('components',n,'triangles',len(f),'positive',sum(r['signed_volume_mm3']>0 for r in rows),'negative',sum(r['signed_volume_mm3']<0 for r in rows));print(json.dumps(rows[:8],indent=2))
