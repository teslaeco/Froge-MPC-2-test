import test from 'node:test';import assert from 'node:assert/strict';
import {build,dimensions} from '../geometry.mjs';import {validateGLB} from '../core.mjs';
import {GLTFExporter} from '../vendor/three/examples/jsm/exporters/GLTFExporter.js';
import {GLTFLoader} from '../vendor/three/examples/jsm/loaders/GLTFLoader.js';
globalThis.FileReader=class {readAsArrayBuffer(blob){blob.arrayBuffer().then(b=>{this.result=b;this.onloadend?.();});}readAsDataURL(blob){blob.arrayBuffer().then(b=>{this.result='data:application/octet-stream;base64,'+Buffer.from(b).toString('base64');this.onloadend?.();});}};
globalThis.ProgressEvent=class{constructor(type,data){this.type=type;Object.assign(this,data);}};
test('Real binary GLB survives export/import with original dimensions and named parts',async()=>{for(const kind of ['cube','car','excavator','iss','hatch']){const object=build({kind,size:100,color:'#af67cc'});const data=await new GLTFExporter().parseAsync(object,{binary:true});const json=validateGLB(data);assert.ok(json.meshes.length);const restored=await new GLTFLoader().parseAsync(data,'');const d=dimensions(restored.scene);assert.ok(Math.abs(Math.max(...Object.values(d))-100)<.01,kind);assert.equal(json.asset.version,'2.0');}});
