import {
  Scene,Color,Group,Mesh,MeshStandardMaterial,MeshBasicMaterial,BoxGeometry,SphereGeometry,
  CylinderGeometry,CapsuleGeometry,TorusGeometry,CanvasTexture,Sprite,SpriteMaterial,
  OrthographicCamera,WebGLRenderer,HemisphereLight,DirectionalLight,PCFSoftShadowMap,
  ACESFilmicToneMapping,SRGBColorSpace,Vector2,Vector3,Raycaster,DoubleSide,
} from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {OFFICE_ROLES,DESKS,officeRoute,employeeVisualState,walkable} from './office3dModel.js';
import {STATUS_LABELS} from './missionView.js';

const COLORS=[0x5498a4,0xd6a35c,0x9682b1,0x659e7a,0xbd7e70,0x6886ab];

export function createOffice3D(host,initial,{onPick,onError}={}) {
  const scene=new Scene();scene.background=new Color('#e9ede7');
  const renderer=new WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.6));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=PCFSoftShadowMap;
  renderer.outputColorSpace=SRGBColorSpace;renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
  renderer.domElement.setAttribute('aria-label','Văn phòng 3D: chọn nhân viên hoặc phòng Agent. Danh sách bàn phím ở bên dưới.');
  renderer.domElement.setAttribute('role','img');host.appendChild(renderer.domElement);
  const camera=new OrthographicCamera(-20,20,16,-16,.1,160);
  camera.position.set(29,32,34);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.target.set(0,.3,0);controls.enableDamping=true;controls.dampingFactor=.09;
  controls.minZoom=.65;controls.maxZoom=3.2;controls.maxPolarAngle=Math.PI*.43;controls.minPolarAngle=.15;
  controls.enablePan=true;controls.rotateSpeed=.55;
  scene.add(new HemisphereLight(0xffffff,0x959786,2.1));
  const sun=new DirectionalLight(0xfff0d3,3.2);sun.position.set(-12,25,14);sun.castShadow=true;
  sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-22,right:22,top:20,bottom:-20,near:1,far:70});
  sun.shadow.normalBias=.035;scene.add(sun);
  const fill=new DirectionalLight(0xe3efff,1.25);fill.position.set(16,14,-15);scene.add(fill);
  const materials=new Map(),geometries=new Map(),textures=new Map();
  function mat(color,options={}){const key=JSON.stringify([color,options]);if(!materials.has(key))materials.set(key,new MeshStandardMaterial({color,roughness:.73,...options}));return materials.get(key);}
  function geometry(key,create){if(!geometries.has(key))geometries.set(key,create());return geometries.get(key);}
  function block(parent,x,y,z,w,h,d,color,options={}){
    const object=new Mesh(geometry(`box:${w}:${h}:${d}`,()=>new BoxGeometry(w,h,d)),mat(color,options));
    object.position.set(x,y,z);object.castShadow=!options.transparent;object.receiveShadow=true;parent.add(object);return object;
  }
  function ball(parent,x,y,z,r,color,sx=1,sy=1,sz=1){
    const object=new Mesh(geometry(`sphere:${r}`,()=>new SphereGeometry(r,14,10)),mat(color));
    object.position.set(x,y,z);object.scale.set(sx,sy,sz);object.castShadow=true;parent.add(object);return object;
  }
  function cylinder(parent,x,y,z,r1,r2,h,color){
    const object=new Mesh(geometry(`cyl:${r1}:${r2}:${h}`,()=>new CylinderGeometry(r1,r2,h,18)),mat(color));
    object.position.set(x,y,z);object.castShadow=true;parent.add(object);return object;
  }
  function text(parent,content,x,y,z,width=3,color='#325659',background='#fffff1'){
    const key=JSON.stringify([content,color,background]);
    if(!textures.has(key)){
      const canvas=document.createElement('canvas');canvas.width=768;canvas.height=150;
      const ctx=canvas.getContext('2d');ctx.fillStyle=background;ctx.beginPath();ctx.roundRect(4,6,760,138,25);ctx.fill();
      ctx.strokeStyle=color;ctx.lineWidth=5;ctx.stroke();ctx.fillStyle=color;ctx.textAlign='center';ctx.textBaseline='middle';
      const fontSize=Math.min(90,Math.max(42,Math.floor(1120/Math.max(content.length,1))));
      ctx.font=`800 ${fontSize}px "Segoe UI",sans-serif`;ctx.fillText(content,384,77,710);
      const texture=new CanvasTexture(canvas);texture.colorSpace=SRGBColorSpace;textures.set(key,texture);
    }
    const object=new Sprite(new SpriteMaterial({map:textures.get(key),depthTest:false,depthWrite:false,transparent:true,toneMapped:false}));
    object.position.set(x,y,z);object.scale.set(width,width*150/768,1);object.renderOrder=10;parent.add(object);return object;
  }
  const labelsToDispose=new Set();
  function replaceLabel(old,parent,...args){if(old){parent.remove(old);old.material.dispose();labelsToDispose.delete(old);}const label=text(parent,...args);labelsToDispose.add(label);return label;}
  function plant(x,z,size=1){
    const g=new Group();scene.add(g);cylinder(g,x,.3,z,.28*size,.22*size,.55,0xcda986);
    cylinder(g,x,.9,z,.05,.06,1.1,0x7c8d54);
    for(let i=0;i<5;i++){const a=i*Math.PI*2/5;const leaf=ball(g,x+Math.cos(a)*.25*size,1.2*size+(i%2)*.15,z+Math.sin(a)*.25*size,.35,0x5d9671,.65,1.6,.45);leaf.rotation.z=Math.sin(a)*.5;}
  }
  function desk(x,z,color=0xd9bd91,parent=scene){
    const g=new Group();parent.add(g);g.position.set(x,0,z);
    block(g,0,.83,0,2.65,.16,1.14,color);[-1.02,1.02].forEach(dx=>block(g,dx,.4,0,.13,.8,.85,0xb3bdbc));
    block(g,0,1.32,-.25,.95,.65,.08,0x34474c);const screen=block(g,0,1.33,-.19,.82,.49,.025,0x78a8af,{emissive:0x6da0ac,emissiveIntensity:.18});
    block(g,0,1,-.25,.08,.25,.08,0x596d6c);block(g,0,.96,-.2,.42,.04,.22,0x566965);
    block(g,0,.94,.24,.75,.04,.26,0xa6aaa1);cylinder(g,.94,1,.19,.1,.085,.22,0xf5f2df);
    block(g,0,.49,1.03,.76,.15,.68,0x677b7a);block(g,0,.89,1.32,.82,.65,.16,0x788e8a);
    cylinder(g,0,.23,1.03,.06,.06,.45,0x5c6a6b);block(g,0,.04,1.03,.9,.06,.12,0x5c6a6b);
    return {root:g,screen};
  }
  function couch(x,z,w=3,color=0xc38e65){
    block(scene,x,.35,z,w,.55,1.1,color);block(scene,x,.83,z-.45,w,.7,.22,color);
    block(scene,x-w/2+.12,.65,z,.24,.6,1.2,color);block(scene,x+w/2-.12,.65,z,.24,.6,1.2,color);
  }
  // A cutaway office: low opaque edges and transparent glass keep all work visible.
  block(scene,0,-.28,0,28.4,.45,23.2,0xb7c7bf);
  block(scene,0,-.025,0,28,.1,23,0xf1e6d0);
  block(scene,-5.5,.035,2,17.1,.07,11.3,0xd7dfe0);
  for(let col=0;col<9;col++)for(let row=0;row<7;row++)if((col+row)%2===0)block(scene,-13.1+col*1.9,.078,-2.8+row*1.6,1.88,.015,1.58,0xe1e6e4);
  for(let row=0;row<10;row++)block(scene,8,.04,-.2+row*.9,8.2,.012,.018,0xd6c3a5);
  block(scene,-14,.25,0,.16,.5,23,0xa6bcb5);block(scene,0,.25,-11.5,28,.5,.15,0xa6bcb5);
  block(scene,14,.25,0,.16,.5,23,0xa6bcb5);
  const rooms=new Map();
  for(const role of OFFICE_ROLES){
    const room=new Group();scene.add(room);room.userData.role=role.id;
    block(room,role.x,.08,-7,5.65,.1,5.25,role.id==='inventory'?0xe6d4b6:0xdce4df);
    block(room,role.x,1.22,-9.6,5.7,2.35,.13,0xc4d2cc);
    for(const x of [role.x-2.8,role.x+2.8]){
      block(room,x,1.15,-7,.07,2.2,5.2,0xa8cbd0,{transparent:true,opacity:.16,depthWrite:false,metalness:.1});
      block(room,x,.13,-7,.09,.18,5.2,0x7d9690);
      block(room,x,2.25,-7,.065,.065,5.2,0x718e88);
      for(const z of [-9.55,-4.5])block(room,x,1.16,z,.065,2.25,.065,0x718e88);
    }
    for(const dx of [-1.95,1.95]){block(room,role.x+dx,1.08,-4.42,1.7,2.1,.055,0xa2c5c8,{transparent:true,opacity:.13,depthWrite:false});block(room,role.x+dx,.13,-4.42,1.7,.16,.08,0x8ba39b);}
    const sign=text(room,role.title,role.x,2.8,-8.7,4.7,role.color);sign.userData.pick={roleId:role.id};
    const station=desk(role.x,-7.8,0xd8c29b,room);
    couch(role.x-1.3,-5.2,1.85,role.id==='report'?0x89aaa1:0xb8bca6);
    room.traverse(o=>{o.userData.pick={roleId:role.id};});rooms.set(role.id,{root:room,station});
  }
  text(scene,'VIỆT TÍN  /  HIVEFIVE',-8.8,1.95,10.3,5.3,'#456e62');
  block(scene,-9.7,.67,9.65,4.3,1.15,1.1,0x86a69a);block(scene,-9.7,1.3,9.65,4.5,.12,1.2,0xf2e6cd);
  text(scene,'VÀO CA',-9.7,1.8,9.6,1.8,'#456e62');
  couch(8.5,1.5,5,0xbda683);couch(8.5,5.1,3.1,0x8ba9a0);
  cylinder(scene,8.5,.38,3.2,.7,.75,.12,0xeadbc1);cylinder(scene,8.5,.2,3.2,.12,.18,.35,0x7c8f86);
  cylinder(scene,8.4,.56,3.2,.1,.08,.2,0xf7f4e7);
  text(scene,'GÓC NGHỈ  /  CHỜ VIỆC',8.5,2.9,1.5,5,'#857355');
  block(scene,11.8,.75,-1.6,1.25,1.5,.8,0x36545c);block(scene,11.8,1.25,-1.16,1,.55,.035,0x87c8bc);
  for(const y of [.35,.58,.81])block(scene,11.8,y,-1.17,.9,.12,.04,0x6e8f93);
  text(scene,'TÀI SẢN LAB',11.8,2.25,-1.6,2.7,'#527980');
  block(scene,5.4,.1,5.5,.08,.18,10.8,0xb6c9c0);
  [-12.8,-6.3,6.4,12.7].forEach(x=>plant(x,-10.4,.85));plant(12.4,7.8,1);plant(5.5,.1,.8);plant(-13,8.2,.8);
  const employeeDesks=DESKS.map(d=>desk(d.x,d.z));
  const peopleRoot=new Group();scene.add(peopleRoot);const people=new Map(),roles=new Map();
  const capsule=geometry('body',()=>new CapsuleGeometry(.26,.48,4,9));
  function avatar(color,robot=false){
    const g=new Group(),body=new Group();g.add(body);
    const shirt=new Mesh(capsule,mat(color));shirt.position.y=.9;body.add(shirt);shirt.castShadow=true;
    if(robot){
      block(body,0,1.5,0,.78,.58,.57,0xf3f5e8);block(body,0,1.5,.3,.6,.36,.035,0x264d4a);
      for(const x of [-.16,.16])ball(body,x,1.52,.34,.06,0x81d6b1);
      cylinder(body,0,1.98,0,.035,.035,.25,0x6eaa96);ball(body,0,2.12,0,.08,0xe8b963);
    }else{
      ball(body,0,1.56,0,.39,0xecc6a4,1,1.05,.93);
      const hair=ball(body,0,1.75,-.035,.4,color===COLORS[1]?0x86634c:0x3b4443,1,.7,.95);
      hair.rotation.x=-.16;
      for(const x of [-.13,.13])ball(body,x,1.57,.345,.035,0x354644);
      block(body,.11,.93,.253,.085,.15,.025,0xf2eee0);
    }
    const arms=[-1,1].map(side=>{const limb=new Group();limb.position.set(side*.34,1.05,0);body.add(limb);block(limb,0,-.19,0,.16,.42,.19,color);ball(limb,0,-.44,0,.105,0xecc6a4);return limb;});
    const legs=[-1,1].map(side=>{const limb=new Group();limb.position.set(side*.14,.58,0);body.add(limb);block(limb,0,-.22,0,.19,.43,.2,0x4d6166);block(limb,0,-.45,.07,.23,.13,.38,0x344b4f);return limb;});
    const ring=new Mesh(geometry('ring',()=>new TorusGeometry(.6,.045,8,40)),mat(0x74a58f));ring.rotation.x=-Math.PI/2;ring.position.y=.025;g.add(ring);
    return {root:g,body,arms,legs,ring,route:[],step:0,label:null,speech:null,tag:'',destination:null,working:false};
  }
  for(const role of OFFICE_ROLES){const actor=avatar(parseInt(role.color.slice(1),16),role.id==='security');scene.add(actor.root);actor.root.position.set(role.x,0,-6.55);actor.root.traverse(o=>o.userData.pick={roleId:role.id});roles.set(role.id,actor);}
  const beam=new Mesh(geometry('scanbeam',()=>new CylinderGeometry(.08,1,1.8,28,1,true)),new MeshBasicMaterial({color:0x76cdb2,transparent:true,opacity:.16,depthWrite:false,side:DoubleSide}));beam.visible=false;scene.add(beam);
  let data=initial,disposed=false,frame,lastTime=performance.now(),elapsed=0,lastPage=-1,selectedId=null,cameraMode='iso',pointerStart=null,lastSocPlan=-1;
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  function moveTo(actor,target){
    const signature=`${target.x.toFixed(2)}:${target.z.toFixed(2)}`;
    if(actor.destination===signature)return;
    actor.destination=signature;
    if(reduced.matches){actor.root.position.set(target.x,0,target.z);actor.route=[];return;}
    actor.route=officeRoute({x:actor.root.position.x,z:actor.root.position.z},target);actor.step=0;
    if(walkable(target.x,target.z)&&actor.route.length)actor.route.push(target);
  }
  function update(next){
    data=next;const snapshot=next.snapshot;
    if(lastPage!==snapshot.page){
      peopleRoot.clear();for(const actor of people.values())for(const label of [actor.label,actor.speech])if(label){label.material.dispose();labelsToDispose.delete(label);}people.clear();lastPage=snapshot.page;
      employeeDesks.forEach((d,i)=>{d.root.visible=i<snapshot.people.length;d.root.traverse(o=>{delete o.userData.pick;});});
    }
    for(const record of snapshot.people){
      let actor=people.get(record.id);
      if(!actor){actor=avatar(COLORS[record.index%COLORS.length]);peopleRoot.add(actor.root);actor.root.position.set(record.destination.x,0,record.destination.z);actor.destination=`${record.destination.x.toFixed(2)}:${record.destination.z.toFixed(2)}`;people.set(record.id,actor);actor.root.traverse(o=>o.userData.pick={employeeId:record.id});employeeDesks[record.index].root.traverse(o=>o.userData.pick={employeeId:record.id});}
      if(!actor.hasMachine&&record.machine){actor.root.position.set(record.destination.x,0,record.destination.z);actor.destination=`${record.destination.x.toFixed(2)}:${record.destination.z.toFixed(2)}`;actor.route=[];}
      actor.hasMachine=Boolean(record.machine);moveTo(actor,record.destination);
      const visual=employeeVisualState(record);actor.ring.material=mat(record.selected?0xd8ab51:visual.color);
      actor.working=record.machine?.state.shift==='on'&&record.machine.state.location==='desk'&&record.machine.state.screen_state==='unlocked';
      const tag=`${record.id}:${visual.label}:${record.selected}`;
      if(actor.tag!==tag){actor.tag=tag;actor.label=replaceLabel(actor.label,actor.root,record.id,0,2.4,0,2.6,visual.color,record.selected?'#fff4d5':'#fffff1');}
      actor.label.userData.pick={employeeId:record.id};
      const screenColor=record.machine?.state.network_isolated?0xd39b64:record.machine?.state.screen_state==='unlocked'?0x72b7b2:0x607b80;
      employeeDesks[record.index].screen.material=mat(screenColor,{emissive:screenColor,emissiveIntensity:.15});
      const speech=record.receipt?.command||'';
      if(speech!==actor.speechText){actor.speechText=speech;if(actor.speech){actor.root.remove(actor.speech);actor.speech.material.dispose();labelsToDispose.delete(actor.speech);actor.speech=null;}if(speech)actor.speech=replaceLabel(null,actor.root,speech,0,3,0,2.6,'#527269','#fffdf3');}
      actor.receiptAt=Date.parse(record.receipt?.observed_at)||0;
      if(actor.speech)actor.speech.userData.pick={employeeId:record.id};
      actor.root.userData.selected=record.selected;
    }
    for(const role of snapshot.roles){
      const actor=roles.get(role.id);actor.working=role.status==='running';
      const textValue=role.id==='security'&&next.liveFocus?.active?'Đang kiểm tra':STATUS_LABELS[role.status]||'Chưa có việc';
      if(actor.tag!==textValue){actor.tag=textValue;actor.label=replaceLabel(actor.label,actor.root,textValue,0,2.65,0,3,role.color);}
      actor.label.userData.pick={roleId:role.id};
      actor.seated=actor.working||role.status==='awaiting_review';
      actor.ring.material=mat(next.selectedRole===role.id?0xd8ab51:role.color);
      if(role.id!=='security')moveTo(actor,actor.seated?{x:role.x,z:-6.55}:{x:role.x-1.3,z:-5.6});
    }
    const selectionChanged=selectedId!==next.selectedEmployee;
    selectedId=next.selectedEmployee;
    if(selectionChanged&&cameraMode==='follow')setCamera('follow');
  }
  function setCamera(mode){cameraMode=mode;const selected=people.get(selectedId);if(mode==='follow'&&selected){const p=selected.root.position;camera.position.set(p.x+13,15,p.z+15);controls.target.set(p.x,0,p.z);camera.zoom=1.2;}else{camera.position.set(mode==='top'?0:29,mode==='top'?44:32,mode==='top'?5:34);controls.target.set(0,.3,0);camera.zoom=1;}camera.updateProjectionMatrix();controls.update();}
  function resize(){const width=Math.max(1,host.clientWidth),height=Math.max(1,host.clientHeight),ratio=width/height,span=Math.max(15,20/ratio);camera.left=-span*ratio;camera.right=span*ratio;camera.top=span;camera.bottom=-span;camera.updateProjectionMatrix();renderer.setSize(width,height,false);}
  const observer=new ResizeObserver(resize);observer.observe(host);resize();
  const ray=new Raycaster(),pointer=new Vector2();
  function pointerDown(e){pointerStart=e.isPrimary===false?null:{x:e.clientX,y:e.clientY};}
  function pointerUp(e){if(!pointerStart||Math.hypot(e.clientX-pointerStart.x,e.clientY-pointerStart.y)>6)return;pointerStart=null;const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);const found=ray.intersectObjects(scene.children,true).find(hit=>{if(!hit.object.userData.pick)return false;let node=hit.object;while(node){if(!node.visible)return false;node=node.parent;}return true;});if(found)onPick?.(found.object.userData.pick);}
  function contextLost(e){e.preventDefault();onError?.('Trình duyệt đã ngắt ngữ cảnh 3D. Chuyển sang sơ đồ để tiếp tục thao tác.');}
  renderer.domElement.addEventListener('pointerdown',pointerDown);renderer.domElement.addEventListener('pointerup',pointerUp);renderer.domElement.addEventListener('webglcontextlost',contextLost);
  function animate(now){
    if(disposed)return;frame=requestAnimationFrame(animate);if(document.hidden){lastTime=now;return;}
    const dt=Math.min((now-lastTime)/1000,.06);lastTime=now;elapsed+=dt;
    for(const actor of [...people.values(),...roles.values()]){
      let walking=false;
      if(actor.step<actor.route.length){const target=actor.route[actor.step];const dx=target.x-actor.root.position.x,dz=target.z-actor.root.position.z,length=Math.hypot(dx,dz);if(length<.05)actor.step++;else{const amount=Math.min(length,dt*3);actor.root.position.x+=dx/length*amount;actor.root.position.z+=dz/length*amount;actor.root.rotation.y=Math.atan2(dx,dz);walking=true;}}
      else if(actor.working)actor.root.rotation.y=Math.PI;
      actor.body.position.y=!reduced.matches&&walking?Math.abs(Math.sin(elapsed*11))*.05:0;
      actor.legs.forEach((leg,i)=>leg.rotation.x=!reduced.matches&&walking?Math.sin(elapsed*11+i*Math.PI)*.48:0);
      actor.arms.forEach((arm,i)=>arm.rotation.x=!reduced.matches&&walking?-Math.sin(elapsed*11+i*Math.PI)*.45:actor.working?-.8+(!reduced.matches?Math.sin(elapsed*5+i)*.08:0):0);
      if(actor.speech)actor.speech.visible=Date.now()-actor.receiptAt<12000;
      actor.ring.scale.setScalar(actor.root.userData.selected&&!reduced.matches?1+Math.sin(elapsed*3)*.045:1);
    }
    const soc=roles.get('security'),focus=data.liveFocus;
    const record=focus?.active?data.snapshot.people.find(p=>p.id===focus.employee_id):null;
    const focusedDesk=record?DESKS[record.index]:null;
    const inspected=focus?.active&&focus.asset_id&&!focus.asset_id.startsWith('OFFICE-')?{x:11.8,z:-1.6}:focusedDesk;
    if(inspected){if(elapsed-lastSocPlan>.8){moveTo(soc,{x:inspected.x+1.2,z:inspected.z+1.4});lastSocPlan=elapsed;}soc.working=true;beam.visible=true;beam.position.set(inspected.x,1.05,inspected.z);}
    else{beam.visible=false;const patrolling=data.monitoring?.active&&!data.liveFocus?.active&&!reduced.matches;const paths=[{x:3,z:-3.5},{x:-7,z:-3.5},{x:3.9,z:7.8}];moveTo(soc,patrolling?paths[Math.floor(elapsed/11)%paths.length]:{x:3,z:-6.55});}
    if(cameraMode==='follow'){const selected=people.get(selectedId);if(selected)controls.target.lerp(new Vector3(selected.root.position.x,0,selected.root.position.z),.08);}
    controls.update();renderer.render(scene,camera);
  }
  update(initial);setCamera('iso');frame=requestAnimationFrame(animate);
  return {update,setCamera,dispose(){disposed=true;cancelAnimationFrame(frame);observer.disconnect();controls.dispose();renderer.domElement.removeEventListener('pointerdown',pointerDown);renderer.domElement.removeEventListener('pointerup',pointerUp);renderer.domElement.removeEventListener('webglcontextlost',contextLost);scene.traverse(o=>{if(o.isSprite)o.material.dispose();});beam.material.dispose();for(const v of materials.values())v.dispose();for(const v of geometries.values())v.dispose();for(const v of textures.values())v.dispose();renderer.dispose();renderer.domElement.remove();}};
}
