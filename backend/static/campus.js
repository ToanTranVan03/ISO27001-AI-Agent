import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {findPath, isWalkable} from './navigation.mjs';

const $ = id => document.getElementById(id);
const DEPARTMENTS = {
  IT: {x: -8.5, y: 6.6, floor: 1, color: '#478ba3', label: 'IT · CÔNG NGHỆ'},
  Ops: {x: 8.5, y: 6.6, floor: 1, color: '#50927c', label: 'OPS · VẬN HÀNH'},
  Finance: {x: -8.5, y: 13.2, floor: 2, color: '#a28b5e', label: 'FINANCE · TÀI CHÍNH'},
  Sales: {x: 8.5, y: 13.2, floor: 2, color: '#ab7390', label: 'SALES · KINH DOANH'}
};

function startCampus() {
  const host = $('campus-canvas');
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: false});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.7));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .98;
  host.append(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#e8ebe3');
  scene.fog = new THREE.Fog('#e8ebe3', 110, 210);
  const camera = new THREE.OrthographicCamera(-28, 28, 20, -20, .1, 250);
  const viewScale = () => Math.max(1, 1.25 / (host.clientWidth / host.clientHeight));
  const overviewPosition = () => new THREE.Vector3(43, 26, 48).multiplyScalar(viewScale()).add(new THREE.Vector3(0, 7, 0));
  camera.position.copy(overviewPosition());
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 7, 0);
  controls.enableDamping = true;
  controls.dampingFactor = .08;
  controls.minDistance = 9;
  controls.maxDistance = 180;
  controls.maxPolarAngle = Math.PI / 2.04;
  controls.minPolarAngle = .12;
  controls.autoRotateSpeed = .45;
  controls.minZoom = .65; controls.maxZoom = 2.4; controls.zoomSpeed = .45;
  scene.add(new THREE.HemisphereLight('#f5f8ff', '#adad93', 1.8));
  const fill = new THREE.DirectionalLight('#e4efff', 1.1); fill.position.set(15, 20, -15); scene.add(fill);
  const sun = new THREE.DirectionalLight('#fff1d9', 2.4);
  sun.position.set(-25, 50, 30);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, {left: -45, right: 45, top: 45, bottom: -45, near: 1, far: 120});
  sun.shadow.bias = -.0005;
  sun.shadow.normalBias = .06;
  sun.shadow.radius = 4;
  scene.add(sun);

  const boxGeometry = new THREE.BoxGeometry(1, 1, 1);
  const sphereGeometry = new THREE.SphereGeometry(1, 24, 18);
  const cylinderGeometry = new THREE.CylinderGeometry(1, 1, 1, 24);
  const hairGeometry = new THREE.SphereGeometry(.53, 12, 8, 0, Math.PI * 2, 0, Math.PI * .54);
  const pickGeometry = new THREE.SphereGeometry(.8, 8, 6);
  const pickMaterial = new THREE.MeshBasicMaterial({visible: false});
  const materials = new Map();
  const material = color => {
    if (!materials.has(color)) materials.set(color, new THREE.MeshStandardMaterial({color, roughness: .72}));
    return materials.get(color);
  };
  const glass = new THREE.MeshStandardMaterial({color: '#9fcece', roughness: .12, metalness: .12, transparent: true, opacity: .2, depthWrite: false});
  function shape(parent, geometry, size, position, color, shadow = true) {
    const mesh = new THREE.Mesh(geometry, typeof color === 'string' ? material(color) : color);
    mesh.scale.set(...size); mesh.position.set(...position);
    mesh.castShadow = shadow; mesh.receiveShadow = true; parent.add(mesh); return mesh;
  }
  const box = (parent, size, position, color, shadow = true) => shape(parent, boxGeometry, size, position, color, shadow);
  const sphere = (parent, size, position, color, shadow = true) => shape(parent, sphereGeometry, size, position, color, shadow);
  const cylinder = (parent, radius, height, position, color) => shape(parent, cylinderGeometry, [radius, height, radius], position, color);
  // Shared beveled geometry gives furniture soft edges without extra downloads.
  const outline = new THREE.Shape();
  outline.moveTo(-.42, -.5); outline.lineTo(.42, -.5); outline.quadraticCurveTo(.5, -.5, .5, -.42);
  outline.lineTo(.5, .42); outline.quadraticCurveTo(.5, .5, .42, .5);
  outline.lineTo(-.42, .5); outline.quadraticCurveTo(-.5, .5, -.5, .42);
  outline.lineTo(-.5, -.42); outline.quadraticCurveTo(-.5, -.5, -.42, -.5);
  const softGeometry = new THREE.ExtrudeGeometry(outline, {depth: .9, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: .04, bevelThickness: .05, curveSegments: 5});
  softGeometry.center(); softGeometry.rotateX(Math.PI / 2);
  const softBox = (parent, size, position, color) => shape(parent, softGeometry, size, position, color);
  const floorCanvas = document.createElement('canvas'); floorCanvas.width = 512; floorCanvas.height = 512;
  const floorContext = floorCanvas.getContext('2d');
  floorContext.fillStyle = '#cbbd9e'; floorContext.fillRect(0, 0, 512, 512);
  for (let row = 0; row < 16; row++) {
    floorContext.fillStyle = ['#d9cdb5', '#dfd3bb', '#d1c3a7', '#e2d6c0'][row % 4];
    floorContext.fillRect(1, row * 32 + 1, 510, 30);
    floorContext.strokeStyle = '#b9a989'; floorContext.lineWidth = .5;
    const seam = (row * 137) % 512;
    floorContext.beginPath(); floorContext.moveTo(seam, row * 32); floorContext.lineTo(seam, row * 32 + 32); floorContext.stroke();
  }
  const floorTexture = new THREE.CanvasTexture(floorCanvas); floorTexture.colorSpace = THREE.SRGBColorSpace;
  floorTexture.wrapS = floorTexture.wrapT = THREE.RepeatWrapping; floorTexture.repeat.set(2, 2);
  floorTexture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const oakFloor = new THREE.MeshStandardMaterial({map: floorTexture, roughness: .78});

  function sign(parent, text, position, width = 6, color = '#214d42', background = '#ffffff') {
    const canvas = document.createElement('canvas'); canvas.width = 768; canvas.height = 128;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = background; ctx.beginPath(); ctx.roundRect(4, 4, 760, 120, 22); ctx.fill();
    ctx.font = '600 48px "Segoe UI", Arial'; ctx.fillStyle = color; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(text, 384, 67, 724);
    const texture = new THREE.CanvasTexture(canvas); texture.colorSpace = THREE.SRGBColorSpace;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: texture, depthTest: false, depthWrite: false, toneMapped: false, fog: false}));
    sprite.scale.set(width, width / 6, 1); sprite.position.set(...position); parent.add(sprite); return sprite;
  }

  function plant(parent, x, y, z, scale = 1) {
    const group = new THREE.Group(); group.position.set(x, y, z); group.scale.setScalar(scale); parent.add(group);
    cylinder(group, .42, .7, [0, .35, 0], '#e5ddcb');
    cylinder(group, .09, .95, [0, 1, 0], '#77694d');
    sphere(group, [.65, .75, .65], [0, 1.7, 0], '#739b67');
    sphere(group, [.45, .6, .45], [.35, 1.4, .15], '#8ca975');
  }

  // One building on Earth: landscaped site, three floors and an optional facade.
  const site = new THREE.Group(); scene.add(site);
  box(site, [65, 1, 51], [0, -1.2, 0], '#b6c8a3');
  box(site, [42, .35, 28], [0, -.55, 0], '#d1d6ca');
  box(site, [9, .15, 18], [0, -.6, 20], '#e9e6db');
  box(site, [65, .1, 6], [0, -.66, 27], '#9ca9a5');
  for (let x = -29; x < 30; x += 7) box(site, [3, .03, .18], [x, -.59, 27], '#e4e6d8', false);
  for (const x of [-26, 26]) for (const z of [-17, -4, 12]) plant(site, x, -.6, z, 2.2);
  for (const x of [-17, 17]) {
    box(site, [7, .6, 2.4], [x, -.2, 18], '#eee7d5');
    for (let n = -2; n <= 2; n++) sphere(site, [.8, .7, .8], [x + n, .4, 18], '#69916d');
    for (const z of [22, -19]) {
      box(site, [4.4, .35, 1.1], [x, .45, z], '#a98761');
      box(site, [.22, .9, .7], [x - 1.7, 0, z], '#3c5750');
      box(site, [.22, .9, .7], [x + 1.7, 0, z], '#3c5750');
    }
  }
  // Small parked vehicles give the architectural model a readable scale.
  for (const [x, color] of [[-24, '#657e83'], [23, '#f0e8ce']]) {
    box(site, [2.3, 1, 4], [x, .15, 21], color);
    box(site, [2, .7, 2.2], [x, .9, 20.8], '#6c9096');
    for (const dx of [-1.2, 1.2]) for (const dz of [-1.1, 1.1]) sphere(site, [.28, .4, .4], [x + dx, -.05, 21 + dz], '#354742');
  }

  const floors = [], facade = new THREE.Group(), roof = new THREE.Group();
  scene.add(facade, roof);
  for (let level = 0; level < 3; level++) {
    const floor = new THREE.Group(); floor.position.y = level * 6.6; scene.add(floor); floors.push(floor);
    box(floor, [36.5, .45, 22], [0, 0, 0], '#f2efe3');
    box(floor, [36.7, .12, 22.2], [0, -.23, 0], '#c2a777');
    box(floor, [35.2, .08, 20.8], [0, .27, 0], level ? '#e4dfce' : '#e8e8df');
    box(floor, [36, 4.9, .3], [0, 2.7, -10.8], '#f4f0e5');
    for (const x of [-17.6, 17.6]) {
      box(floor, [.5, 6.1, .6], [x, 3, -10.2], '#e6e4d8');
      box(floor, [.5, 6.1, .6], [x, 3, 10.2], '#e6e4d8');
    }
    box(floor, [.22, 1.7, 20], [0, 1.1, 0], glass, false);
    for (const x of [-17.8, 17.8]) box(floor, [.18, 3.5, 20.6], [x, 2.1, 0], glass, false);
    for (let index = 0; index <= 6; index++) {
      const x = -17.4 + index * 5.8;
      box(facade, [.14, 6.1, .16], [x, level * 6.6 + 3.1, 10.7], '#496a66');
      if (index < 6) box(facade, [5.6, 5.7, .07], [x + 2.9, level * 6.6 + 3.1, 10.7], glass, false);
    }
    if (level) {
      plant(floor, -16, .3, 8.3, .8); plant(floor, 16, .3, 8.3, .8);
    }
  }
  // Lobby: reception, training/meeting room, and visible server racks.
  const lobby = floors[0];
  box(lobby, [10, 1.5, 2.2], [0, 1, 6.5], '#316c5a');
  box(lobby, [10.4, .18, 2.5], [0, 1.85, 6.5], '#ddd0aa');
  sign(lobby, 'HIVEFIVE  /  RECEPTION', [0, 3.5, 7], 9);
  for (let i = 0; i < 3; i++) {
    box(lobby, [2.1, 3.4, 1.6], [-13 + i * 3, 2, -6.8], '#254d48');
    for (let row = 0; row < 5; row++) {
      box(lobby, [1.6, .33, .08], [-13 + i * 3, .85 + row * .55, -5.95], '#52746a');
      sphere(lobby, [.07, .07, .07], [-12.4 + i * 3, .85 + row * .55, -5.85], '#a4da9a', false);
    }
  }
  sign(lobby, 'PHÒNG MÁY CHỦ · IT', [-10, 5, -7], 8);
  box(lobby, [9, .25, 3], [10, 1.6, -3], '#c7ae83');
  for (const x of [7, 10, 13]) for (const z of [-5.3, -.8]) {
    box(lobby, [1.5, .25, 1.4], [x, .85, z], '#6c9281');
    box(lobby, [1.5, 1.4, .2], [x, 1.4, z + .6], '#6c9281');
  }
  sign(lobby, 'HR · ĐÀO TẠO & NHẬN THỨC', [10, 4.7, -5.3], 9);
  for (const x of [-15, 15]) plant(lobby, x, .3, 6, 1.3);
  box(lobby, [5, .2, 3], [-11, .5, 4], '#e7c977');
  box(lobby, [5, 1, 1.1], [-11, 1.2, 4.9], '#ba916f');
  sign(lobby, 'TẦNG 1 / ĐÓN TIẾP · HR · IT', [0, 5.3, 10], 10);

  // Rooftop garden, pergola and solar panels remain part of the same building.
  roof.position.y = 19.8;
  box(roof, [37, .5, 22.8], [0, 0, 0], '#f2efe5');
  box(roof, [37.2, .12, 23], [0, -.25, 0], '#c6a773');
  for (const x of [-17.5, 17.5]) box(roof, [.3, .9, 22], [x, .65, 0], '#e2e3d5');
  for (const z of [-10.5, 10.5]) box(roof, [35, .9, .3], [0, .65, z], '#e2e3d5');
  box(roof, [14, .2, 14], [-8, .4, 0], '#93b081');
  for (const x of [-13, -3]) for (const z of [-5, 5]) cylinder(roof, .14, 3, [x, 1.9, z], '#c9ae7e');
  for (let x = -13; x <= -3; x += 1) box(roof, [.38, .2, 11], [x, 3.5, 0], '#cab68f');
  for (const x of [-12, -5]) plant(roof, x, .4, 6, 1.1);
  for (const x of [5, 11]) for (const z of [-5, 2]) {
    const solar = box(roof, [5, .14, 5], [x, .9, z], '#355e76'); solar.rotation.x = -.18;
    for (let dx = -1.6; dx <= 1.7; dx += 1.6) box(roof, [.03, .05, 4.8], [x + dx, 1.1, z], '#89b1bb', false);
  }
  sign(roof, 'HIVEFIVE', [0, 2.5, 11.5], 11, '#214d42', '#f4d788');
  const rooms = new Map(), obstacles = new Map();
  const roomBounds = {minX: -8.1, maxX: 8.1, minZ: -9.1, maxZ: 9.1};
  for (const [department, config] of Object.entries(DEPARTMENTS)) {
    const room = new THREE.Group(); room.position.y = config.y; scene.add(room); rooms.set(department, room);
    obstacles.set(department, []);
    softBox(room, [17.8, .65, 20.3], [config.x, -.15, 0], '#b2b79f');
    box(room, [17.3, .12, 19.8], [config.x, .23, 0], oakFloor);
    box(room, [17.5, 1.6, .28], [config.x, 1.02, -9.9], '#f5f0e5');
    box(room, [.28, 3.6, 20], [config.x - 8.65, 2, 0], '#dbe2d5');
    box(room, [.1, .18, 19.9], [config.x - 8.47, .42, 0], '#b9bea9');
    for (const x of [-5, 2]) {
      box(room, [5.6, 2.3, .15], [config.x + x, 2.95, -9.95], '#4e6c62');
      box(room, [5.3, 2.06, .16], [config.x + x, 2.95, -9.84], '#c8dfdd');
      for (const dx of [-.9, .9]) box(room, [.055, 2.1, .18], [config.x + x + dx, 2.95, -9.72], '#769085');
      box(room, [5.6, .12, .4], [config.x + x, 1.85, -9.7], '#f5f0e5');
    }
    // Built-in cabinet and acoustic wall detail stay outside the walking area.
    softBox(room, [.35, 1.5, 5], [config.x - 8.28, 1.05, 5.2], '#688878');
    for (let z = 3.3; z < 7.2; z += 1) box(room, [.025, 1.15, .025], [config.x - 8.08, 1.1, z], '#b1c0a8');
    for (let z = -6; z < -.5; z += .32) box(room, [.09, 2.3, .1], [config.x - 8.45, 2, z], '#b7ac8b');
    plant(room, config.x - 7.6, .3, -8.7, .85);
    plant(room, config.x + 7.6, .3, -8.7, .85);
    box(room, [.7, .04, 17], [config.x + 7.6, .32, 0], '#a4b49c', false);
  }
  // Reusable desktop geometry.
  function desk(parent, x, z) {
    softBox(parent, [3.2, .16, 1.55], [x, 1.28, z], '#dfd1b6');
    for (const dx of [-1.3, 1.3]) {
      box(parent, [.08, 1, .75], [x + dx, .74, z], '#576c61');
      softBox(parent, [.45, .08, 1], [x + dx, .29, z], '#576c61');
    }
    softBox(parent, [1.6, .018, .95], [x, 1.38, z + .03], '#9ba99a');
    box(parent, [.06, .35, .08], [x, 1.56, z - .28], '#53685f');
    softBox(parent, [1.15, .72, .08], [x, 1.91, z - .26], '#314f48');
    box(parent, [1.02, .58, .02], [x, 1.91, z - .20], '#b6d5d1', false);
    for (let i = 0; i < 3; i++) box(parent, [.64 - i * .1, .035, .025], [x -.08, 2.06 - i * .1, z - .182], '#e6f0e6', false);
    softBox(parent, [.9, .045, .3], [x, 1.42, z + .37], '#e6e9df');
    softBox(parent, [.32, .035, .46], [x + 1.05, 1.4, z + .24], '#b48b6f');
    cylinder(parent, .12, .22, [x - 1.1, 1.48, z + .2], '#f4f1de');
    cylinder(parent, .09, .01, [x - 1.1, 1.6, z + .2], '#80604a');
    // A complete chair reads as furniture rather than a floating block.
    cylinder(parent, .055, .47, [x, .5, z + .64], '#5b6a61');
    for (const angle of [0, Math.PI / 2]) {
      const foot = box(parent, [.82, .06, .08], [x, .3, z + .64], '#5b6a61'); foot.rotation.y = angle;
    }
    softBox(parent, [.88, .15, .75], [x, .76, z + .64], '#6c8b7b');
    softBox(parent, [.88, .72, .13], [x, 1.13, z + .98], '#6c8b7b');
  }
  for (const [department, config] of Object.entries(DEPARTMENTS)) {
    const room = rooms.get(department);
    sign(room, `HIVEFIVE / ${department}`, [config.x, 4.75, -9.3], 6, '#456754', '#f9f9ef');
  }

  const peopleRoot = new THREE.Group(); scene.add(peopleRoot);
  const avatars = new Map(), pickTargets = [];
  const selectedRing = new THREE.Mesh(new THREE.TorusGeometry(.85, .06, 8, 36), material('#248ac0'));
  selectedRing.rotation.x = Math.PI / 2; selectedRing.visible = false; scene.add(selectedRing);
  const raycaster = new THREE.Raycaster(), pointer = new THREE.Vector2();
  let dataset = null, selectedId = '', activeView = 'Sales', interior = false, lastDraw = 0;
  let cameraGoal = null, targetGoal = null;
  const movingBadges = [];
  let route = [], goalMarker = null;
  const pressed = new Set();
  goalMarker = new THREE.Mesh(new THREE.TorusGeometry(.45, .05, 8, 28), material('#d8a92e'));
  goalMarker.rotation.x = Math.PI / 2; goalMarker.visible = false; scene.add(goalMarker);

  // =========================================================================
  // 3D AI AGENT AUDITOR BOT (KIỂM TOÁN VIÊN AI TRỰC QUAN TRONG KHÔNG GIAN 3D)
  // =========================================================================
  const agentBotGroup = new THREE.Group();
  scene.add(agentBotGroup);

  const botBody = new THREE.Mesh(sphereGeometry, new THREE.MeshStandardMaterial({color: '#0e7490', roughness: .25, metalness: .8}));
  botBody.scale.set(.65, .55, .65); agentBotGroup.add(botBody);

  const botEye = new THREE.Mesh(cylinderGeometry, new THREE.MeshBasicMaterial({color: '#22d3ee'}));
  botEye.scale.set(.48, .12, .48); botEye.rotation.x = Math.PI / 2; botEye.position.set(0, 0, .28);
  agentBotGroup.add(botEye);

  const botRing = new THREE.Mesh(new THREE.TorusGeometry(.85, .05, 8, 32), new THREE.MeshBasicMaterial({color: '#38bdf8'}));
  botRing.rotation.x = Math.PI / 2; botRing.position.y = -.25;
  agentBotGroup.add(botRing);

  const botAntenna = new THREE.Mesh(cylinderGeometry, new THREE.MeshStandardMaterial({color: '#64748b'}));
  botAntenna.scale.set(.04, .45, .04); botAntenna.position.set(0, .45, 0);
  const botLight = new THREE.Mesh(sphereGeometry, new THREE.MeshBasicMaterial({color: '#10b981'}));
  botLight.scale.set(.12, .12, .12); botLight.position.set(0, .68, 0);
  agentBotGroup.add(botAntenna, botLight);

  const scanConeGeometry = new THREE.CylinderGeometry(.25, 1.85, 3.2, 24, 1, true);
  scanConeGeometry.translate(0, -1.6, 0);
  const scanConeMaterial = new THREE.MeshBasicMaterial({color: '#06b6d4', transparent: true, opacity: .32, depthWrite: false, side: THREE.DoubleSide});
  const botScanBeam = new THREE.Mesh(scanConeGeometry, scanConeMaterial);
  botScanBeam.visible = false; agentBotGroup.add(botScanBeam);

  const floorRingMaterial = new THREE.MeshBasicMaterial({color: '#06b6d4', transparent: true, opacity: .65});
  const botFloorRing = new THREE.Mesh(new THREE.TorusGeometry(1.6, .06, 8, 32), floorRingMaterial);
  botFloorRing.rotation.x = Math.PI / 2; botFloorRing.visible = false; scene.add(botFloorRing);

  let botBadge = sign(agentBotGroup, '🤖 AI AGENT: ĐANG TUẦN TRA', [0, 1.4, 0], 5.6, '#ffffff', '#0f766e');
  let currentBotLabel = 'patrol';
  let botTargetPos = new THREE.Vector3(8.5, 16.5, -3.0);
  agentBotGroup.position.copy(botTargetPos);

  function updateAgentBotSign(text, color, bg) {
    if (botBadge) {
      agentBotGroup.remove(botBadge);
      if (botBadge.material && botBadge.material.map) {
        botBadge.material.map.dispose();
        botBadge.material.dispose();
      }
    }
    botBadge = sign(agentBotGroup, text, [0, 1.4, 0], 5.8, color, bg);
  }

  function avatar(parent, person, index, isAffected, controlNames) {
    const config = DEPARTMENTS[person.department];
    const column = index % 3, row = Math.floor(index / 3);
    const x = config.x + (column - 1) * 4.6, z = -7.3 + row * 3.2;
    if (!desksBuilt) {
      desk(rooms.get(person.department), x, z);
      obstacles.get(person.department).push({minX: x - config.x - 1.95, maxX: x - config.x + 1.95, minZ: z - 1.15, maxZ: z + 1.15});
    }
    const group = new THREE.Group(); group.position.set(x, config.y + .1, z + 1.65); parent.add(group);
    const shirt = isAffected ? (person.status === 'terminated' ? '#d9381e' : '#e78b43') : config.color;
    const skin = ['#e2b38a', '#b98561', '#f0c8a4', '#d8a479'][Number(person.id.slice(-3)) % 4];
    sphere(group, [.37, .51, .29], [0, 1.12, 0], shirt);
    cylinder(group, .14, .2, [0, 1.6, 0], skin);
    sphere(group, [.52, .54, .49], [0, 1.94, 0], skin);
    const hair = new THREE.Mesh(hairGeometry, material(index % 3 ? '#4b3e34' : '#71614c'));
    hair.position.set(0, 2.03, -.03); group.add(hair);
    const legs = [];
    for (const dx of [-.18, .18]) {
      sphere(group, [.06, .075, .04], [dx, 1.94, .46], '#253f39', false);
      legs.push(box(group, [.22, .48, .26], [dx, .48, .05], '#405960'));
      sphere(group, [.16, .4, .17], [dx * 2.8, 1.1, .07], shirt);
      sphere(group, [.12, .13, .12], [dx * 2.8, .78, .07], skin);
      softBox(group, [.26, .14, .42], [dx, .24, .14], '#efe9db');
    }
    sphere(group, [.065, .035, .025], [0, 1.78, .475], '#ba7c67', false);
    box(group, [.018, .38, .025], [0, 1.24, .28], '#e5e7d8', false);
    softBox(group, [.16, .21, .025], [.16, 1.1, .29], '#f3e8c8');
    if (isAffected) {
      let badgeLabel = 'CẦN XỬ LÝ';
      let badgeColor = '#ffe0ac';
      let textColor = '#794320';
      if (person.status === 'terminated') {
        badgeLabel = 'NGHỈ VIỆC · CHƯA BÀN GIAO';
        badgeColor = '#fcd0cf';
        textColor = '#a81c15';
      } else if (person.remote && controlNames.includes('A.6.7')) {
        badgeLabel = 'TỪ XA · CHƯA MÃ HÓA';
        badgeColor = '#fee3c6';
        textColor = '#944410';
      } else if (controlNames.includes('A.6.3')) {
        badgeLabel = 'CHƯA ĐÀO TẠO ATTT';
      } else if (controlNames.includes('A.6.6')) {
        badgeLabel = 'THIẾU CAM KẾT NDA';
      }
      const badge = sign(group, badgeLabel, [0, 3.1, 0], 4.2, textColor, badgeColor);
      movingBadges.push({badge, base: 3.1, offset: index, personId: person.id});
    }
    const pick = new THREE.Mesh(pickGeometry, pickMaterial);
    pick.position.y = 1.6; pick.userData.personId = person.id; group.add(pick); pickTargets.push(pick);
    avatars.set(person.id, {group, config, person, head: hair, phase: index, legs});
  }

  // Desks are static between scenario runs; rebuild only avatars/badges on updates.
  let desksBuilt = false;
  function updateData(detail) {
    dataset = detail;
    route = []; pressed.clear(); if (goalMarker) goalMarker.visible = false;
    while (peopleRoot.children.length) {
      const root = peopleRoot.children[0];
      root.traverse(obj => {
        if (obj.isSprite) {obj.material.map.dispose(); obj.material.dispose();}
      });
      peopleRoot.remove(root);
    }
    avatars.clear(); pickTargets.length = 0; movingBadges.length = 0;
    const counts = {};
    // Populate fixed desks once while avatar state refreshes for every scenario.
    const affectedSet = new Set(detail.affected);
    for (const person of detail.enterprise.people) {
      const index = counts[person.department] || 0; counts[person.department] = index + 1;
      const controlsForPerson = detail.controls.filter(c => c.findings.some(f => f.person_id === person.id) || c.missing_evidence.includes(person.id)).map(c => c.control_id);
      avatar(peopleRoot, person, index, affectedSet.has(person.id), controlsForPerson);
    }
    desksBuilt = true;
    $('person-select').replaceChildren(new Option('Chọn một nhân vật…', ''), ...detail.enterprise.people.map(p => new Option(`${p.id} · ${p.department}`, p.id)));
    $('scene-status').textContent = `${detail.affected.length} nhân sự cần xử lý`;
    $('scene-status').dataset.affected = String(detail.affected.length);
    $('scene-status').dataset.ready = 'true';
    $('scene-scenario').textContent = detail.scenario?.name || 'Doanh nghiệp mẫu';
    const focusPerson = detail.enterprise.people.find(p => affectedSet.has(p.id));
    const person = focusPerson || detail.enterprise.people.find(p => p.department === 'Sales');
    applyView(person.department, true);
    selectPerson(person.id, false);
  }

  function text(tag, value) {const node = document.createElement(tag); node.textContent = value; return node;}
  function selectPerson(id, focus = true) {
    route = []; pressed.clear(); if (goalMarker) goalMarker.visible = false;
    avatars.get(selectedId)?.legs.forEach(leg => {leg.rotation.x = 0;});
    selectedId = id; $('person-select').value = id;
    const record = avatars.get(id); selectedRing.visible = !!record;
    if (!record || !dataset) {
      $('person-detail').textContent = 'Chọn nhân sự trong danh sách hoặc bấm nhân vật để xem hồ sơ.';
      return;
    }
    selectedRing.position.copy(record.group.position); selectedRing.position.y += .07;
    const person = record.person, detail = $('person-detail');
    detail.replaceChildren(text('h3', person.name), text('p', `${person.id} · ${person.department} · Tầng ${record.config.floor + 1}`));
    const problems = dataset.controls.filter(c => c.findings.some(f => f.person_id === id));
    const status = text('div', problems.length ? problems.map(c => `${c.control_id}: ${c.name}`).join(' · ') : 'Hồ sơ mẫu đầy đủ theo quy tắc đang mô phỏng.');
    status.className = `inspector-status${problems.length ? '' : ' clear'}`; detail.append(status);
    detail.append(text('h4', 'CON NGƯỜI'), text('p', `Đào tạo: ${person.training_complete && person.training_passed ? 'Hoàn tất' : 'Chưa hoàn tất'} · NDA: ${person.nda_signed ? 'Đã ký' : 'Chưa ký'}`), text('p', `Trạng thái: ${person.status === 'terminated' ? 'Đã nghỉ việc' : 'Đang làm việc'}${person.remote ? ' · Làm từ xa' : ''}`));
    detail.append(text('h4', 'PHẦN MỀM'));
    const accounts = text('ul', '');
    for (const account of dataset.enterprise.accounts.filter(a => a.person_id === id)) accounts.append(text('li', `${account.system}: ${account.active ? 'Đang mở' : 'Đã khóa'} · ${account.mfa ? 'Có MFA' : 'Thiếu MFA'}`));
    detail.append(accounts, text('h4', 'PHẦN CỨNG'));
    for (const device of dataset.enterprise.devices.filter(d => d.person_id === id)) detail.append(text('p', `${device.id} · ${device.encrypted ? 'Đã mã hóa' : 'Chưa mã hóa'} · ${device.returned ? 'Đã trả' : 'Đang giữ'}`));
    for (const control of problems) detail.append(text('h4', `PHỤ TRÁCH: ${control.owner}`), text('p', control.recommended_action));
    for (const item of movingBadges) {
      item.badge.visible = true;
      const isSelected = item.personId === id;
      item.badge.scale.set(isSelected ? 5.2 : 3.8, (isSelected ? 5.2 : 3.8) / 6, 1);
    }
    host.dataset.personId = id;
    $('movement-status').textContent = `Đang điều khiển ${id}. Bấm vị trí trống trên sàn để đi, hoặc dùng WASD / phím mũi tên.`;
    window.dispatchEvent(new CustomEvent('hivefive:person-selected', {detail: {person}}));
    if (focus) {
      applyView(person.department, true);
    }
  }

  function applyView(view, move = true) {
    activeView = view;
    const config = DEPARTMENTS[view];
    route = []; pressed.clear(); if (goalMarker) goalMarker.visible = false;
    floors.forEach(floor => {floor.visible = !config; floor.traverse(obj => {if (obj.isSprite) obj.visible = interior && !config;});});
    for (const [department, room] of rooms) {
      room.visible = !config || department === view;
      room.children.filter(child => child.isSprite).forEach(label => {label.visible = !!config;});
    }
    site.visible = !config;
    for (const {group, person} of avatars.values()) group.visible = !config || person.department === view;
    roof.visible = !interior && !config;
    facade.visible = !interior && !config;
    if (move) {
      camera.zoom = 1;
      targetGoal = config ? new THREE.Vector3(config.x, config.y + 1, 0) : new THREE.Vector3(0, 7, 0);
      cameraGoal = config ? targetGoal.clone().add(new THREE.Vector3(18, 25, 22)) : overviewPosition();
    }
    selectedRing.visible = !!selectedId && (!config || avatars.get(selectedId)?.person.department === view);
    $('campus-title').textContent = config ? `${config.label.replace(' · ', ' / ')} · Tầng ${config.floor + 1}` : 'Toàn cảnh tòa nhà HiveFive';
    host.dataset.view = view;
    updateProjection();
    for (const button of document.querySelectorAll('[data-view]')) button.setAttribute('aria-pressed', String(button.dataset.view === view));
  }

  function updateProjection() {
    const aspect = host.clientWidth / host.clientHeight;
    const span = Math.max(activeView === 'all' ? 25 : 9.3, (activeView === 'all' ? 29 : 12) / aspect);
    camera.left = -span * aspect; camera.right = span * aspect;
    camera.top = span; camera.bottom = -span; camera.updateProjectionMatrix();
  }

  function walkTo(worldPoint) {
    const record = avatars.get(selectedId);
    if (!record || activeView !== record.person.department) {
      $('movement-status').textContent = 'Chọn một phòng và một nhân vật trước khi di chuyển.'; return;
    }
    const start = {x: record.group.position.x - record.config.x, z: record.group.position.z};
    const goal = {x: worldPoint.x - record.config.x, z: worldPoint.z};
    route = findPath(start, goal, roomBounds, obstacles.get(record.person.department));
    if (!route.length) {
      goalMarker.visible = false;
      $('movement-status').textContent = 'Vị trí bị chắn hoặc ngoài phòng. Hãy bấm vào lối đi trống.'; return;
    }
    controls.autoRotate = false; $('rotate-scene').setAttribute('aria-pressed', 'false'); $('rotate-scene').textContent = 'Tự xoay: tắt';
    goalMarker.position.set(worldPoint.x, record.config.y + .3, worldPoint.z); goalMarker.visible = true;
    $('movement-status').textContent = `${selectedId} đang đi tới vị trí đã chọn…`;
  }

  function moveCharacter(dt, now) {
    const record = avatars.get(selectedId);
    if (!record || activeView !== record.person.department) {host.dataset.moving = 'false'; return;}
    const origin = record.group.position.clone();
    let direction = new THREE.Vector3(), stride = 3.2 * dt;
    if (pressed.size) {
      route = []; goalMarker.visible = false;
      const forward = camera.getWorldDirection(new THREE.Vector3()); forward.y = 0; forward.normalize();
      const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0));
      if (pressed.has('up')) direction.add(forward);
      if (pressed.has('down')) direction.sub(forward);
      if (pressed.has('left')) direction.sub(right);
      if (pressed.has('right')) direction.add(right);
      direction.normalize();
    } else if (route.length) {
      const point = route[0];
      direction.set(point.x + record.config.x - origin.x, 0, point.z - origin.z);
      const distance = direction.length();
      if (distance < .04) {route.shift(); direction.set(0, 0, 0);} else {stride = Math.min(stride, distance); direction.normalize();}
      if (!route.length) {goalMarker.visible = false; $('movement-status').textContent = `${selectedId} đã đến nơi. Di chuyển chỉ minh họa, không thay đổi kết quả ISO.`;}
    }
    const point = {x: origin.x - record.config.x, z: origin.z};
    const blocks = obstacles.get(record.person.department);
    const nextX = {x: point.x + direction.x * stride, z: point.z};
    if (isWalkable(nextX, roomBounds, blocks)) point.x = nextX.x;
    const nextZ = {x: point.x, z: point.z + direction.z * stride};
    if (isWalkable(nextZ, roomBounds, blocks)) point.z = nextZ.z;
    record.group.position.x = point.x + record.config.x; record.group.position.z = point.z;
    const delta = record.group.position.clone().sub(origin), walking = delta.length() > .0001;
    if (walking) {
      record.group.rotation.y = Math.atan2(delta.x, delta.z);
      record.legs.forEach((leg, i) => {leg.rotation.x = Math.sin(now * .013 + i * Math.PI) * .45;});
    } else record.legs.forEach(leg => {leg.rotation.x = 0;});
    selectedRing.position.copy(record.group.position); selectedRing.position.y = record.config.y + .3;
    host.dataset.personX = record.group.position.x.toFixed(3); host.dataset.personZ = record.group.position.z.toFixed(3);
    host.dataset.moving = String(walking || route.length > 0);
  }

  $('person-select').addEventListener('change', event => selectPerson(event.target.value));
  window.addEventListener('hivefive:focus-person', event => {if (avatars.has(event.detail.id)) selectPerson(event.detail.id);});
  for (const button of document.querySelectorAll('[data-view]')) button.addEventListener('click', () => {
    applyView(button.dataset.view);
    if (DEPARTMENTS[button.dataset.view] && avatars.get(selectedId)?.person.department !== button.dataset.view) {
      const person = dataset.enterprise.people.find(p => p.department === button.dataset.view); selectPerson(person.id, false);
    }
  });
  $('focus-scene').addEventListener('click', () => {
    const person = dataset?.enterprise.people.find(p => dataset.affected.includes(p.id)) || avatars.get(selectedId)?.person;
    if (person) selectPerson(person.id);
  });
  const focusAgentBtn = $('focus-agent');
  if (focusAgentBtn) {
    focusAgentBtn.addEventListener('click', () => {
      if (agentBotGroup) {
        cameraGoal = agentBotGroup.position.clone().add(new THREE.Vector3(14, 12, 16));
        targetGoal = agentBotGroup.position.clone();
      }
    });
  }
  window.addEventListener('hivefive:guide-step', event => {if (event.detail.step === 1 && selectedId) selectPerson(selectedId);});
  $('interior-scene').addEventListener('click', () => {
    interior = !interior; $('interior-scene').setAttribute('aria-pressed', String(interior));
    $('interior-scene').textContent = `Nội thất: ${interior ? 'bật' : 'tắt'}`; applyView(activeView, false);
  });
  $('rotate-scene').addEventListener('click', () => {
    controls.autoRotate = !controls.autoRotate;
    $('rotate-scene').setAttribute('aria-pressed', String(controls.autoRotate));
    $('rotate-scene').textContent = `Tự xoay: ${controls.autoRotate ? 'bật' : 'tắt'}`;
  });
  controls.addEventListener('start', () => {cameraGoal = null; targetGoal = null;});
  let pointerStart = null;
  renderer.domElement.addEventListener('pointerdown', event => {pointerStart = [event.clientX, event.clientY];});
  renderer.domElement.addEventListener('pointerup', event => {
    if (!pointerStart || Math.hypot(event.clientX - pointerStart[0], event.clientY - pointerStart[1]) > 6) return;
    const bounds = renderer.domElement.getBoundingClientRect();
    pointer.set((event.clientX - bounds.left) / bounds.width * 2 - 1, -(event.clientY - bounds.top) / bounds.height * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(pickTargets.filter(p => p.parent.visible))[0];
    host.focus({preventScroll: true});
    if (hit) {selectPerson(hit.object.userData.personId); return;}
    const record = avatars.get(selectedId);
    if (record && activeView !== 'all') {
      const point = new THREE.Vector3();
      if (raycaster.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 1, 0), -record.config.y - .25), point)) walkTo(point);
    }
  });
  const keyDirections = {KeyW: 'up', ArrowUp: 'up', KeyS: 'down', ArrowDown: 'down', KeyA: 'left', ArrowLeft: 'left', KeyD: 'right', ArrowRight: 'right'};
  window.addEventListener('keydown', event => {
    if (document.activeElement !== host || !keyDirections[event.code]) return;
    event.preventDefault(); pressed.add(keyDirections[event.code]);
  });
  window.addEventListener('keyup', event => {if (keyDirections[event.code]) pressed.delete(keyDirections[event.code]);});
  window.addEventListener('blur', () => pressed.clear()); host.addEventListener('blur', () => pressed.clear());
  for (const button of document.querySelectorAll('[data-move]')) {
    button.addEventListener('pointerdown', event => {event.preventDefault(); host.focus({preventScroll: true}); button.setPointerCapture(event.pointerId); pressed.add(button.dataset.move);});
    for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(name, () => pressed.delete(button.dataset.move));
  }
  const resize = new ResizeObserver(() => {
    const width = host.clientWidth, height = host.clientHeight;
    if (!width || !height) return;
    renderer.setSize(width, height); updateProjection();
    if (activeView === 'all' && !selectedId) {
      camera.position.copy(overviewPosition()); controls.target.set(0, 7, 0);
    }
  });
  resize.observe(host);
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  renderer.setAnimationLoop(now => {
    if (document.hidden || now - lastDraw < 32) return;
    const dt = Math.min((now - lastDraw) / 1000, .05); lastDraw = now;
    if (cameraGoal) {
      camera.position.lerp(cameraGoal, reduceMotion ? 1 : .09);
      controls.target.lerp(targetGoal, reduceMotion ? 1 : .09);
      if (camera.position.distanceTo(cameraGoal) < .025) {cameraGoal = null; targetGoal = null;}
    }
    if (!reduceMotion) for (const item of movingBadges) item.badge.position.y = item.base + Math.sin(now * .002 + item.offset) * .08;
    if (!reduceMotion) for (const record of avatars.values()) record.head.rotation.z = Math.sin(now * .0008 + record.phase) * .035;

    // AI Agent Auditor Bot Real-time 3D Animation & Scanning
    if (agentBotGroup) {
      let inspectTarget = null;
      if (selectedId && avatars.has(selectedId)) {
        inspectTarget = avatars.get(selectedId);
      }
      if ((!inspectTarget || !dataset?.affected?.includes(selectedId)) && dataset?.affected?.length) {
        const firstAffectedId = dataset.affected[0];
        if (avatars.has(firstAffectedId)) {
          inspectTarget = avatars.get(firstAffectedId);
        }
      }

      const hasIssue = inspectTarget && dataset?.affected?.includes(inspectTarget.person.id);

      if (inspectTarget) {
        botTargetPos.set(inspectTarget.group.position.x, inspectTarget.config.y + 3.4, inspectTarget.group.position.z);
      } else {
        const activeRoom = DEPARTMENTS[activeView] || DEPARTMENTS.Sales;
        botTargetPos.set(activeRoom.x, activeRoom.y + 3.8, -1.0);
      }

      agentBotGroup.position.lerp(botTargetPos, .045);
      agentBotGroup.position.y += Math.sin(now * .0035) * .008;
      botRing.rotation.z += .04;

      if (hasIssue) {
        botScanBeam.visible = true;
        botFloorRing.visible = true;
        botFloorRing.position.set(agentBotGroup.position.x, inspectTarget.config.y + .05, agentBotGroup.position.z);
        const pulse = 1.0 + Math.sin(now * .006) * .15;
        botFloorRing.scale.set(pulse, pulse, pulse);

        if (inspectTarget.person.status === 'terminated') {
          scanConeMaterial.color.set('#ef4444');
          floorRingMaterial.color.set('#ef4444');
          botLight.material.color.set('#ef4444');
          if (currentBotLabel !== 'term_' + inspectTarget.person.id) {
            currentBotLabel = 'term_' + inspectTarget.person.id;
            updateAgentBotSign(`🔍 AGENT PHÁT HIỆN: ${inspectTarget.person.id} CHƯA BÀN GIAO`, '#ffffff', '#b91c1c');
          }
        } else {
          scanConeMaterial.color.set('#06b6d4');
          floorRingMaterial.color.set('#06b6d4');
          botLight.material.color.set('#f59e0b');
          if (currentBotLabel !== 'issue_' + inspectTarget.person.id) {
            currentBotLabel = 'issue_' + inspectTarget.person.id;
            updateAgentBotSign(`🔍 AGENT ĐANG QUÉT: ${inspectTarget.person.id} CẦN XỬ LÝ`, '#ffffff', '#0369a1');
          }
        }
      } else {
        if (currentBotLabel.startsWith('issue_') || currentBotLabel.startsWith('term_')) {
          botScanBeam.visible = true;
          botFloorRing.visible = true;
          scanConeMaterial.color.set('#10b981');
          floorRingMaterial.color.set('#10b981');
          botLight.material.color.set('#10b981');
          updateAgentBotSign(`✅ AGENT XÁC MINH: ĐÃ KHẮC PHỤC · ĐẠT CHUẨN`, '#ffffff', '#047857');
          currentBotLabel = 'resolved_recent';
          setTimeout(() => {currentBotLabel = 'patrol';}, 3500);
        } else if (currentBotLabel !== 'resolved_recent') {
          botScanBeam.visible = false;
          botFloorRing.visible = false;
          botLight.material.color.set('#10b981');
          if (currentBotLabel !== 'patrol') {
            currentBotLabel = 'patrol';
            updateAgentBotSign('🤖 AI AGENT: ĐANG TUẦN TRA AN TOÀN', '#ffffff', '#0f766e');
          }
        }
      }
    }

    moveCharacter(dt, now);
    host.dataset.cameraMoving = String(!!cameraGoal);
    controls.update(); renderer.render(scene, camera);
  });
  window.addEventListener('hivefive:data', event => updateData(event.detail));
  window.dispatchEvent(new Event('hivefive:scene-ready'));
}

try {startCampus();} catch (error) {
  $('scene-status').textContent = '3D chưa sẵn sàng';
  $('scene-error').textContent = 'Không khởi tạo được đồ họa 3D. Hãy bật tăng tốc đồ họa hoặc dùng Edge/Chrome hỗ trợ WebGL 2. Bạn vẫn có thể chạy tình huống và xem bảng nhân sự bên dưới.';
  $('scene-error').hidden = false;
  console.warn('HiveFive 3D:', error.message);
}
