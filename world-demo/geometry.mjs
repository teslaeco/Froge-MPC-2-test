import * as THREE from './vendor/three/build/three.module.min.js';
import {spec} from './core.mjs';
export function build(input){
  const p=spec(input),g=new THREE.Group();g.name=p.kind;g.userData.spec=p;
  const colored=new THREE.MeshStandardMaterial({color:p.color,roughness:.46,metalness:.22});
  const dark=new THREE.MeshStandardMaterial({color:'#202d3d',roughness:.72});
  const white=new THREE.MeshStandardMaterial({color:'#dce4e8',metalness:.35,roughness:.4});
  const glass=new THREE.MeshStandardMaterial({color:'#173e65',metalness:.65,roughness:.16});
  const solar=new THREE.MeshStandardMaterial({color:'#18397d',metalness:.6,roughness:.32});
  const add=(geometry,pos=[0,0,0],mat=colored,rotation=[0,0,0],name='part')=>{const m=new THREE.Mesh(geometry,mat);m.position.set(...pos);m.rotation.set(...rotation);m.name=name;m.castShadow=true;m.receiveShadow=true;g.add(m);return m;};
  const box=(size,pos,mat,name)=>add(new THREE.BoxGeometry(...size),pos,mat,undefined,name);
  const cyl=(r,h,pos,mat,rot,name)=>add(new THREE.CylinderGeometry(r,r,h,p.detail),pos,mat,rot,name);
  const sphere=(r,pos,mat,name)=>add(new THREE.SphereGeometry(r,p.detail,p.detail/2),pos,mat,undefined,name);
  switch(p.kind){
    case 'cube':box([1,1,1],[0,.5,0]);break;
    case 'sphere':sphere(.5,[0,.5,0]);break;
    case 'cylinder':cyl(.4,1,[0,.5,0]);break;
    case 'prism':add(new THREE.CylinderGeometry(.5,.5,1,p.sides),[0,.5,0]);break;
    case 'cone':add(new THREE.ConeGeometry(.5,1,p.detail),[0,.5,0]);break;
    case 'torus':add(new THREE.TorusGeometry(.36,.14,24,p.detail*2),[0,.5,0]);break;
    case 'icosahedron':add(new THREE.IcosahedronGeometry(.6),[0,.6,0]);break;
    case 'octahedron':add(new THREE.OctahedronGeometry(.6),[0,.6,0]);break;
    case 'house':{
      box([2,1.4,1.7],[0,.7,0],white,'ściany');
      const roof=new THREE.CylinderGeometry(1.38,1.38,2.2,3);add(roof,[0,1.75,0],colored,[Math.PI/2,0,Math.PI/2],'dach');
      box([.4,.85,.07],[.45,.425,.87],dark,'drzwi');
      for(const x of [-.55,.5])box([.4,.4,.04],[x,1,.89],glass,'okno');
      box([.24,.7,.24],[.55,2,-.2],white,'komin');break;}
    case 'car':
      box([1.9,.45,.9],[0,.46,0],colored,'nadwozie');box([.94,.43,.78],[-.1,.9,0],glass,'kabina');
      for(const x of [-.63,.63])for(const z of [-.49,.49]){cyl(.26,.15,[x,.26,z],dark,[Math.PI/2,0,0],'koło');cyl(.12,.17,[x,.26,z],white,[Math.PI/2,0,0],'felga');}
      for(const z of [-.3,.3])box([.04,.12,.2],[.97,.51,z],white,'reflektor');break;
    case 'excavator':
      for(const z of [-.48,.48])box([1.6,.35,.28],[0,.22,z],dark,'gąsienica');
      cyl(.4,.16,[0,.48,0],white);box([1,.42,.8],[-.15,.72,0],colored,'platforma');box([.5,.62,.7],[-.45,1.15,0],glass,'kabina');
      add(new THREE.BoxGeometry(.25,1.25,.25),[.43,1.35,0],colored,[0,0,-.65],'ramię');
      add(new THREE.BoxGeometry(.18,1.15,.18),[1.02,1.34,0],colored,[0,0,.5],'wysięgnik');box([.58,.34,.65],[1.25,.72,0],dark,'łyżka');break;
    case 'astronaut':
      box([.65,.8,.38],[0,1.12,0],white,'korpus');sphere(.33,[0,1.86,0],white,'hełm');
      const visor=sphere(.27,[0,1.87,.16],glass,'wizjer');visor.scale.set(1,.75,.6);
      for(const x of [-.22,.22]){cyl(.14,.67,[x,.48,0],white,undefined,'noga');box([.3,.17,.44],[x,.1,.08],dark,'but');}
      for(const x of [-.49,.49]){cyl(.12,.7,[x,1.12,0],white,[0,0,x*.4],'ręka');sphere(.14,[x*1.1,.75,0],colored,'rękawica');}
      box([.48,.6,.3],[0,1.18,-.3],dark,'plecak');break;
    case 'iss':
      box([7,.14,.14],[0,1.3,0],white,'kratownica');
      for(const x of [-2.8,-1.7,1.7,2.8])for(const z of [-1.15,1.15]){
        box([.7,.07,1.8],[x,1.3,z],solar,'panel słoneczny');
        for(let i=0;i<9;i++)box([.705,.075,.008],[x,1.3,z-.78+i*.19],white,'linia ogniw');
      }
      for(const z of [-.8,0,.8])cyl(.32,.8,[0,1.3,z],white,[Math.PI/2,0,0],'moduł');
      cyl(.3,1.7,[.75,1.3,0],white,[0,0,Math.PI/2],'laboratorium');
      sphere(.33,[0,1.3,1.32],glass,'kopuła');break;
    case 'hatch':
      cyl(.5,.09,[0,.08,0],white);add(new THREE.TorusGeometry(.4,.045,16,64),[0,.14,0],dark,[Math.PI/2,0,0],'uszczelka');
      for(let i=0;i<8;i++)cyl(.025,.1,[Math.cos(i*Math.PI/4)*.46,.12,Math.sin(i*Math.PI/4)*.46],colored);box([.3,.08,.07],[0,.19,0],colored,'uchwyt');break;
    case 'radiator':
      box([1.8,.1,1],[0,.08,0],white);for(let i=0;i<12;i++)box([.04,.14,.95],[-.8+i*.145,.19,0],colored,'żebro');break;
    case 'antenna':
      cyl(.07,.8,[0,.4,0],white);add(new THREE.SphereGeometry(.5,48,24,0,Math.PI*2,0,Math.PI/2),[0,.78,0],colored,[Math.PI,0,0],'czasza');break;
    case 'tree':cyl(.13,1.2,[0,.6,0],dark,undefined,'pień');sphere(.65,[0,1.35,0],colored,'korona');sphere(.45,[.34,1.6,0],colored);break;
    case 'board':
      box([4,.15,4],[0,.075,0],colored,'podstawa');for(let x=0;x<8;x++)for(let z=0;z<8;z++)box([.49,.04,.49],[-1.75+x*.5,.17,-1.75+z*.5],(x+z)%2?dark:white,`pole-${x}-${z}`);break;
  }
  g.updateMatrixWorld(true);const b=new THREE.Box3().setFromObject(g),d=b.getSize(new THREE.Vector3()),scale=(p.size/1000)/Math.max(d.x,d.y,d.z);
  const c=b.getCenter(new THREE.Vector3());for(const child of g.children){child.position.x-=c.x;child.position.y-=b.min.y;child.position.z-=c.z;child.position.multiplyScalar(scale);child.scale.multiplyScalar(scale);}
  g.updateMatrixWorld(true);return g;
}
export function dimensions(object){object.updateMatrixWorld(true);const s=new THREE.Box3().setFromObject(object).getSize(new THREE.Vector3());return {x:s.x*1000,y:s.y*1000,z:s.z*1000};}
export function inspect(object){let triangles=0,meshes=0;const textures=new Map();object.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;for(const m of [o.material].flat()){for(const [k,v]of Object.entries(m))if(v?.isTexture&&v.image)textures.set(v.uuid,{map:k,width:v.image.width,height:v.image.height});}}});return{meshes,triangles,dimensions:dimensions(object),textures:[...textures.values()],printApproved:false,note:'Zamknięcie i suma objętości części nie potwierdzają gotowości do druku; sprawdź połączenia i grubości.'};}
export function neutral(object,enabled,wireframe=false){object.traverse(o=>{if(!o.isMesh)return;if(!o.userData.originalMaterial)o.userData.originalMaterial=o.material;
  if(enabled){o.userData.clay??=new THREE.MeshStandardMaterial({color:'#bfcbd5',roughness:.9});o.material=o.userData.clay;}else o.material=o.userData.originalMaterial;
  for(const m of [o.material].flat())m.wireframe=wireframe;
});}
