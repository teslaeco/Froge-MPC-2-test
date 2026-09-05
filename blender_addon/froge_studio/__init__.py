bl_info = {'name':'Froge Studio — Codex + Local AI','author':'Froge MPC / Codex','version':(1,0,0),'blender':(4,2,0),'location':'3D View > Sidebar > Froge','description':'Import agent models and generate editable geometry with a local Ollama model. No paid cloud API.','category':'3D View'}
import json
import queue
import threading
import urllib.request
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from .geometry import compile_shapes, validate_scene, texture_pixels, SHAPE_SCHEMA

_results=queue.Queue()
_running=False
_generation=0
_collection=None

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError('Przekierowania poza lokalne Ollama sa zablokowane.')

# urllib is deliberately pinned to loopback; no arbitrary URL or generated code.
def local_request(path, payload=None, timeout=180):
    request=urllib.request.Request('http://127.0.0.1:11434'+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=timeout) as response:
        data=response.read(8*1024*1024+1)
        if len(data)>8*1024*1024: raise ValueError('Odpowiedz AI przekracza 8 MB.')
        return json.loads(data)

def build_scene(value):
    global _collection
    scene=validate_scene(value)
    collection=bpy.data.collections.new('Froge · '+scene['name'])
    bpy.context.scene.collection.children.link(collection)
    made_materials=[];made_images=[]
    try:
        for part in scene['parts']:
            # Convert Y-up centimetres into Blender Z-up metres (proper rotation).
            p=part['vertices'];vertices=[(p[i]/100,-p[i+2]/100,p[i+1]/100) for i in range(0,len(p),3)]
            faces=[part['triangles'][i:i+3] for i in range(0,len(part['triangles']),3)]
            mesh=bpy.data.meshes.new(part['name']);mesh.from_pydata(vertices,[],faces);mesh.update()
            obj=bpy.data.objects.new(part['name'],mesh);collection.objects.link(obj)
            uv=mesh.uv_layers.new(name='UVMap')
            for polygon in mesh.polygons:
                polygon.use_smooth=True
                for index in polygon.loop_indices:
                    vertex=mesh.loops[index].vertex_index;uv.data[index].uv=part['uv'][vertex*2:vertex*2+2]
            material=bpy.data.materials.new(part['name']+' Material');made_materials.append(material);material.use_nodes=True
            bsdf=material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=part['roughness'];bsdf.inputs['Metallic'].default_value=part['metalness']
            image=bpy.data.images.new(part['name']+' Texture',width=128,height=128,alpha=True);made_images.append(image)
            image.colorspace_settings.name='sRGB';image.pixels.foreach_set(texture_pixels(part['color'],part['pattern']));image.pack()
            node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
            material.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color']);mesh.materials.append(material)
        collection['froge_scene']=json.dumps(scene,ensure_ascii=False)
        _collection=collection
        bpy.context.scene.unit_settings.system='METRIC'
        return collection
    except Exception:
        for obj in list(collection.objects):
            mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
            if mesh.users==0:bpy.data.meshes.remove(mesh)
        bpy.data.collections.remove(collection)
        for material in made_materials:
            if material.users==0:bpy.data.materials.remove(material)
        for image in made_images:
            if image.users==0:bpy.data.images.remove(image)
        raise

def poll_result():
    global _running
    try:token,scene,error=_results.get_nowait()
    except queue.Empty:return .3 if _running else None
    if token!=_generation:return .3 if _running else None
    _running=False
    try:
        if error:raise ValueError(error)
        build_scene(scene);bpy.context.scene.froge_status='Gotowe. Model w nowej kolekcji Froge.'
    except Exception as error:bpy.context.scene.froge_status='Blad: '+str(error)[:240]
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:area.tag_redraw()
    return None

class FROGE_OT_import(bpy.types.Operator,ImportHelper):
    bl_idname='froge.import_scene';bl_label='Wczytaj scene / polecenie JSON';bl_options={'REGISTER','UNDO'}
    filename_ext='.json'
    filter_glob:StringProperty(default='*.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            with open(self.filepath,'rb') as file:data=file.read(16*1024*1024+1)
            if len(data)>16*1024*1024:raise ValueError('Limit pliku 16 MB.')
            value=json.loads(data)
            if isinstance(value,dict) and value.get('type')=='froge-modeling-request':
                prompt=value.get('prompt')
                if not isinstance(prompt,str) or not 1<=len(prompt)<=2000:raise ValueError('Nieprawidlowe polecenie.')
                context.scene.froge_prompt=prompt;context.scene.froge_status='Polecenie wczytane. Kliknij Generuj lokalnie.'
            else:build_scene(value);context.scene.froge_status='Scena wczytana. Dotychczasowe obiekty pozostaly na miejscu.'
            return {'FINISHED'}
        except Exception as error:self.report({'ERROR'},str(error));return {'CANCELLED'}

class FROGE_OT_models(bpy.types.Operator):
    bl_idname='froge.find_models';bl_label='Sprawdz lokalne modele'
    def execute(self,context):
        try:
            models=local_request('/api/tags',timeout=5).get('models',[])
            names=[m['name'] for m in models if not m.get('remote_host') and not m['name'].endswith('-cloud') and ':cloud' not in m['name']]
            if not names:raise ValueError('Brak lokalnego modelu. Zainstaluj model w Ollama na tym komputerze.')
            context.scene.froge_model=names[0];context.scene.froge_status='Lokalne modele: '+', '.join(names)[:200];return {'FINISHED'}
        except Exception as error:self.report({'ERROR'},'Ollama: '+str(error));return {'CANCELLED'}

class FROGE_OT_generate(bpy.types.Operator):
    bl_idname='froge.generate';bl_label='Generuj lokalnie';bl_description='Uzywa zainstalowanego modelu Ollama na tym komputerze'
    @classmethod
    def poll(cls,context):return not _running
    def execute(self,context):
        global _running,_generation
        prompt=context.scene.froge_prompt.strip();model=context.scene.froge_model.strip()
        if not prompt or not model:self.report({'ERROR'},'Wpisz opis i wybierz zainstalowany model Ollama.');return {'CANCELLED'}
        _running=True;_generation+=1;token=_generation
        context.scene.froge_status='Lokalne AI projektuje geometrie. To moze potrwac kilka minut.'
        def worker():
            try:
                installed=local_request('/api/tags',timeout=5).get('models',[])
                if not any(m.get('name')==model and not m.get('remote_host') and not model.endswith('-cloud') and ':cloud' not in model for m in installed):raise ValueError('Wybierz model lokalny; modele chmurowe nie sa obslugiwane.')
                system='You are a 3D modeler. Design the requested object as a detailed composition, not a single placeholder. Return only JSON following this schema. Units are centimeters; Y is up. sphere and box: center and full size [x,y,z]. tube: points [x,y,z,positive_radius], use many points for smooth curves. mesh: flat vertices and CCW triangle indices. Colors #RRGGBB; patterns solid/scales/bark. Target a 10 cm model unless requested otherwise. Parts may intersect, so output is a modeling draft, not print-ready. Use no code, URLs or file paths. Schema: '+json.dumps(SHAPE_SCHEMA)
                response=local_request('/api/chat',{'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'format':SHAPE_SCHEMA,'stream':False,'options':{'temperature':.2,'num_predict':12000}})
                scene=compile_shapes(json.loads(response['message']['content']))
                _results.put((token,scene,None))
            except Exception as error:_results.put((token,None,str(error)))
        threading.Thread(target=worker,daemon=True).start()
        if not bpy.app.timers.is_registered(poll_result):bpy.app.timers.register(poll_result,first_interval=.3)
        return {'FINISHED'}

class FROGE_OT_cancel(bpy.types.Operator):
    bl_idname='froge.cancel';bl_label='Odrzuc wynik zadania'
    def execute(self,context):
        global _generation,_running
        _generation+=1;_running=False;context.scene.froge_status='Wynik zostanie odrzucony. Ollama moze jeszcze konczyc obliczenia.';return {'FINISHED'}

class FROGE_OT_export(bpy.types.Operator,ExportHelper):
    bl_idname='froge.export_glb';bl_label='Eksportuj ostatni model GLB'
    filename_ext='.glb'
    filter_glob:StringProperty(default='*.glb',options={'HIDDEN'})
    def execute(self,context):
        global _collection
        if _collection is None or _collection.name not in bpy.data.collections:self.report({'ERROR'},'Najpierw wczytaj lub wygeneruj model.');return {'CANCELLED'}
        selected=list(context.selected_objects);active=context.view_layer.objects.active
        try:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in _collection.objects:obj.select_set(True)
            bpy.ops.export_scene.gltf(filepath=self.filepath,export_format='GLB',use_selection=True)
            return {'FINISHED'}
        except Exception as error:self.report({'ERROR'},str(error));return {'CANCELLED'}
        finally:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected:obj.select_set(True)
            context.view_layer.objects.active=active

class FROGE_PT_panel(bpy.types.Panel):
    bl_label='Froge Studio';bl_idname='FROGE_PT_panel';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Froge'
    def draw(self,context):
        layout=self.layout;s=context.scene
        layout.label(text='Codex: wczytaj przygotowana scene')
        layout.operator('froge.import_scene')
        layout.separator();layout.label(text='Darmowe AI: lokalne Ollama')
        layout.prop(s,'froge_prompt',text='Opis');layout.prop(s,'froge_model',text='Model')
        layout.operator('froge.find_models')
        layout.operator('froge.generate')
        if _running:layout.operator('froge.cancel')
        for start in range(0,len(s.froge_status),48):layout.label(text=s.froge_status[start:start+48])
        layout.separator();layout.operator('froge.export_glb')
        layout.label(text='Zapisz .blend: File > Save As')
        layout.label(text='Przed drukiem sprawdz i scal siatke.')

classes=(FROGE_OT_import,FROGE_OT_models,FROGE_OT_generate,FROGE_OT_cancel,FROGE_OT_export,FROGE_PT_panel)
def register():
    for cls in classes:bpy.utils.register_class(cls)
    bpy.types.Scene.froge_prompt=StringProperty(name='Opis',maxlen=2000)
    bpy.types.Scene.froge_model=StringProperty(name='Model Ollama',maxlen=200)
    bpy.types.Scene.froge_status=StringProperty(default='Wczytaj scene od Codexa lub polacz lokalne Ollama.')
def unregister():
    global _running,_generation
    _running=False;_generation+=1
    if bpy.app.timers.is_registered(poll_result):bpy.app.timers.unregister(poll_result)
    for name in ('froge_prompt','froge_model','froge_status'):delattr(bpy.types.Scene,name)
    for cls in reversed(classes):bpy.utils.unregister_class(cls)
if __name__=='__main__':register()
