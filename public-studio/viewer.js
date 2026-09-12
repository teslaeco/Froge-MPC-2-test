import * as THREE from './vendor/three/build/three.module.min.js';
import { DRACOLoader } from './vendor/three/examples/jsm/loaders/DRACOLoader.js';
import { GLTFLoader } from './vendor/three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from './vendor/three/examples/jsm/controls/OrbitControls.js';

export async function openModel(url,host,onProgress){
 const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
 host.replaceChildren(renderer.domElement);const scene=new THREE.Scene();scene.background=new THREE.Color('#232a2f');const camera=new THREE.PerspectiveCamera(32,1,.01,100);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.8;controls.maxDistance=8;renderer.domElement.setAttribute('aria-label','Obrotowy model 3D. Przeciągnij, aby zmienić widok.');
 scene.add(new THREE.HemisphereLight(0xe8f2ff,0x726956,2.8));const key=new THREE.DirectionalLight(0xffedd9,3.5);key.position.set(-3,4,5);scene.add(key);const fill=new THREE.DirectionalLight(0xd3e5ff,1.7);fill.position.set(3,2,-3);scene.add(fill);
 const draco=new DRACOLoader();draco.setDecoderPath('/vendor/three/examples/jsm/libs/draco/gltf/');draco.setWorkerLimit(2);const loader=new GLTFLoader();loader.setDRACOLoader(draco);const gltf=await loader.loadAsync(url,e=>onProgress(e.total?Math.round(e.loaded/e.total*100):null));const model=gltf.scene;scene.add(model);let box=new THREE.Box3().setFromObject(model);const size=box.getSize(new THREE.Vector3());const scale=2/Math.max(size.x,size.y,size.z);model.scale.multiplyScalar(scale);box=new THREE.Box3().setFromObject(model);const center=box.getCenter(new THREE.Vector3());model.position.sub(center);camera.position.set(0,.12,4.2);controls.target.set(0,0,0);controls.update();
 const resize=()=>{const width=host.clientWidth,height=host.clientHeight;if(!width||!height)return;renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix()};new ResizeObserver(resize).observe(host);resize();renderer.setAnimationLoop(()=>{if(host.hidden||document.hidden)return;controls.update();renderer.render(scene,camera)});return renderer;
}
