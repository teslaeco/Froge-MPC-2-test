"""Dedicated globe-local eye UVs, with one frontal iris per anatomical globe."""
import bpy,numpy as np

def apply_eye_albedo(objects, iris_color=(.075,.031,.014)):
 n=512
 yy,xx=np.mgrid[-1:1:complex(n),-1:1:complex(n)]
 r=np.sqrt(xx*xx+yy*yy);angle=np.arctan2(yy,xx)
 fibers=.85+.12*np.sin(angle*97+r*87)+.08*np.sin(angle*173-r*58)
 rgb=np.asarray(iris_color);rgb=np.array([.10,.055,.026]) if rgb.mean()>.65 else rgb
 rgb=np.where(rgb<=.0031308,rgb*12.92,1.055*np.maximum(rgb,0)**(1/2.4)-.055)
 iris=rgb[None,None,:]*fibers[:,:,None]
 pixels=np.ones((n,n,4),dtype=np.float32)
 pixels[:,:,:3]=[.69,.67,.635]
 pixels[:,:,:3]=np.where((r<.405)[:,:,None],iris,pixels[:,:,:3])
 pixels[:,:,:3]=np.where(((r>.37)&(r<.425))[:,:,None],np.array([.020,.012,.008]),pixels[:,:,:3])
 pixels[:,:,:3]=np.where((r<.180)[:,:,None],.003,pixels[:,:,:3])
 image=bpy.data.images.new('anatomical-dedicated-iris',width=n,height=n,alpha=False)
 image.pixels.foreach_set(pixels.reshape(-1));image.update();image.file_format='PNG';image.pack()
 mat=bpy.data.materials.new('anatomical-coherent-eye');mat.use_nodes=True
 bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.24
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='EXTEND'
 uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='EyeLocal'
 mat.node_tree.links.new(uvnode.outputs['UV'],tex.inputs['Vector']);mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
 count=0
 for obj in objects:
  if obj.type!='MESH' or not obj.name.startswith('anatomical-eye-'):continue
  layer=obj.data.uv_layers.get('EyeLocal') or obj.data.uv_layers.new(name='EyeLocal')
  for polygon in obj.data.polygons:
   front=sum(obj.data.vertices[i].co.y for i in polygon.vertices)<0
   for li in polygon.loop_indices:
    v=obj.data.vertices[obj.data.loops[li].vertex_index].co
    layer.data[li].uv=(v.x*.49+.5,v.z*.49+.5) if front else (.02,.02)
  obj.data.uv_layers.active=layer
  for candidate in obj.data.uv_layers:candidate.active_render=candidate==layer
  obj.data.materials.clear();obj.data.materials.append(mat)
  obj['iris_count']=1;obj['gaze_direction']=[0,-1,0]
  count+=1
 return count

