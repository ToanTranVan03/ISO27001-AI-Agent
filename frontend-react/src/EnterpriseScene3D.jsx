import { useEffect, useRef } from "react";
import {
  ACESFilmicToneMapping, BoxGeometry, BufferGeometry, CanvasTexture, CapsuleGeometry,
  Clock, Color, CylinderGeometry, DirectionalLight, Fog, GridHelper,
  Group, HemisphereLight, Line, LineDashedMaterial,
  Mesh, MeshBasicMaterial, MeshStandardMaterial, OctahedronGeometry, PCFSoftShadowMap,
  PerspectiveCamera, PlaneGeometry, PointLight, Scene, SphereGeometry, Sprite,
  SpriteMaterial, SRGBColorSpace, TorusGeometry, Vector3, WebGLRenderer,
} from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

const AREAS = {
  people: { title: "CON NGƯỜI · TRỤ SỞ", color: 0xffb777, position: [-5.1, 0, 0], size: [4.9, 3.3] },
  hardware: { title: "PHẦN CỨNG · KHO THIẾT BỊ", color: 0x78d7e9, position: [0, 0, -2.2], size: [4.1, 3.1] },
  software: { title: "PHẦN MỀM · TRUNG TÂM CNTT", color: 0xc4b5ff, position: [5.1, 0, 0], size: [4.1, 3.1] },
};

function material(color, options = {}) {
  return new MeshStandardMaterial({ color, roughness: 0.68, metalness: 0.08, ...options });
}

function box(parent, position, size, color, options = {}) {
  const mesh = new Mesh(new BoxGeometry(...size), material(color, options));
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}

function labelSprite(text, color) {
  const canvas = document.createElement("canvas");
  canvas.width = 768;
  canvas.height = 160;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "rgba(13, 25, 40, .91)";
  ctx.beginPath();
  ctx.roundRect(8, 8, 752, 144, 34);
  ctx.fill();
  ctx.strokeStyle = `#${color.toString(16).padStart(6, "0")}`;
  ctx.lineWidth = 7;
  ctx.stroke();
  ctx.fillStyle = "#f4f7fb";
  ctx.font = "900 36px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, 384, 80, 690);
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  const sprite = new Sprite(new SpriteMaterial({ map: texture, transparent: true, depthTest: false }));
  sprite.scale.set(4.4, 0.92, 1);
  return sprite;
}

function makePerson(parent, x, z, scale = 1) {
  const group = new Group();
  group.position.set(x, 0.44, z);
  group.scale.setScalar(scale);
  const jacket = material(0xf08b58);
  const skin = material(0xf0c6a1);
  const body = new Mesh(new CapsuleGeometry(0.22, 0.48, 4, 8), jacket);
  body.position.y = 0.65;
  body.castShadow = true;
  group.add(body);
  const head = new Mesh(new SphereGeometry(0.2, 16, 12), skin);
  head.position.y = 1.2;
  head.castShadow = true;
  group.add(head);
  const hair = new Mesh(new SphereGeometry(0.205, 16, 8, 0, Math.PI * 2, 0, Math.PI * 0.47), material(0x35475a));
  hair.position.y = 1.24;
  group.add(hair);
  const arms = [-1, 1].map((side) => {
    const arm = new Mesh(new CapsuleGeometry(0.075, 0.28, 3, 6), jacket);
    arm.position.set(side * 0.28, 0.73, 0.02);
    arm.rotation.z = side * -0.38;
    arm.castShadow = true;
    group.add(arm);
    return arm;
  });
  group.userData.actionArms = arms;
  parent.add(group);
  return group;
}

function buildArea(scene, key, area) {
  const group = new Group();
  group.position.set(...area.position);
  scene.add(group);
  const width = area.size[0];
  const depth = area.size[1];
  const front = depth / 2;
  const accentMaterial = material(area.color, { emissive: area.color, emissiveIntensity: 0.16, roughness: 0.4 });
  let activityWorker = null;
  let laptopScreen = null;
  let usbDrive = null;
  let activityLabel = null;
  let resolvedActivityLabel = null;

  // Building cutaway: real facade, structural columns, upper windows and a
  // partial roof keep the interior visible while reading as three buildings.
  box(group, [0, 0.18, 0], [width + 0.28, 0.32, depth + 0.28], 0xb9c4c5);
  box(group, [0, 0.38, -depth * 0.12], [width, 0.12, depth * 0.76], 0xe1d7c7);
  box(group, [0, 1.48, -depth / 2 + 0.09], [width, 2.18, 0.18], key === "hardware" ? 0x83949a : 0x8ea5ae);
  box(group, [-width / 2 + 0.09, 1.45, -0.05], [0.18, 2.08, depth - 0.2], 0xaebdc0);
  box(group, [width / 2 - 0.09, 1.45, -0.05], [0.18, 2.08, depth - 0.2], 0xaebdc0);

  // Window bands and mullions on the side walls.
  for (const side of [-1, 1]) {
    for (let row = 0; row < 2; row += 1) {
      const windowPane = box(group, [side * (width / 2 - 0.185), 1.15 + row * 0.78, 0.16], [0.035, 0.55, 0.88], 0x6e9aa5, { transparent: true, opacity: 0.68, metalness: 0.18, roughness: 0.24 });
      windowPane.castShadow = false;
      box(group, [side * (width / 2 - 0.16), 1.15 + row * 0.78, 0.16], [0.045, 0.035, 0.92], 0xd5e0dc);
    }
  }

  // Front glass, vertical frame, double entry door and an illuminated canopy.
  [-1, 1].forEach((side) => {
    const pane = box(group, [side * width * 0.28, 1.43, front - 0.025], [width * 0.34, 1.9, 0.055], 0x6da0ae, { transparent: true, opacity: 0.34, metalness: 0.2, roughness: 0.18 });
    pane.castShadow = false;
    box(group, [side * width * 0.28, 1.43, front + 0.014], [0.045, 1.92, 0.045], 0xd5e0dc);
    box(group, [side * 0.55, 1.43, front + 0.016], [0.035, 1.9, 0.045], 0xd5e0dc);
  });
  box(group, [0, 1.2, front + 0.04], [0.78, 1.45, 0.06], 0x608a97, { transparent: true, opacity: 0.32, metalness: 0.25, roughness: 0.2 });
  box(group, [0, 1.94, front + 0.05], [1.45, 0.12, 0.56], area.color, { emissive: area.color, emissiveIntensity: 0.25 });
  box(group, [0, 2.72, -depth * 0.19], [width + 0.22, 0.24, depth * 0.62], 0x667982, { metalness: 0.25, roughness: 0.42 });
  box(group, [0, 2.86, front - 0.12], [width + 0.22, 0.08, 0.16], area.color, { emissive: area.color, emissiveIntensity: 0.32 });

  // Rooftop utility detail and mounted company sign.
  box(group, [width * 0.28, 2.98, -depth * 0.34], [0.64, 0.22, 0.5], 0x87979a, { metalness: 0.22 });
  [-0.15, 0, 0.15].forEach((offset) => box(group, [width * 0.28 + offset, 3.1, -depth * 0.34], [0.035, 0.04, 0.38], 0x465d66));
  const title = labelSprite(area.title, area.color);
  title.scale.set(Math.min(width * 0.92, 4.4), 0.62, 1);
  title.position.set(0, 3.36, front + 0.12);
  group.add(title);
  const focusLight = new PointLight(area.color, 0.25, 6);
  focusLight.position.set(0, 3, 0.2);
  group.add(focusLight);
  const accent = new MeshBasicMaterial({ color: area.color, transparent: true, opacity: 0.6 });
  const canopy = new Mesh(new BoxGeometry(width + 0.22, 0.08, 0.14), accent);
  canopy.position.set(0, 2.86, front - 0.12);
  canopy.castShadow = false;
  group.add(canopy);

  if (key === "people") {
    // Reception, employee workstations, access turnstiles and staff figures.
    box(group, [-1.22, 0.61, -0.34], [1.18, 0.12, 0.68], 0x9a7658);
    box(group, [-1.22, 0.92, -0.52], [0.68, 0.46, 0.07], 0x273a4b, { metalness: 0.2 });
    box(group, [-1.22, 0.94, -0.475], [0.58, 0.32, 0.02], 0x75cbd3, { emissive: 0x2b9fb0, emissiveIntensity: 0.22 });
    box(group, [0.72, 0.57, -0.46], [1.08, 0.1, 0.54], 0xb58b67);
    box(group, [0.72, 0.82, -0.57], [0.62, 0.38, 0.055], 0x273a4b);
    [-0.85, -0.34].forEach((x) => box(group, [x, 0.62, 0.62], [0.08, 0.42, 0.08], 0x596d77));
    box(group, [-0.6, 0.84, 0.62], [0.42, 0.045, 0.05], 0xd5e1d9);
    makePerson(group, -0.15, 0.48, 0.75);
    makePerson(group, 1.34, -0.45, 0.74);
    makePerson(group, -1.66, 0.7, 0.68);
  } else if (key === "hardware") {
    // Shelved inventory, tagged endpoints and logistics cartons.
    [-1.25, 1.18].forEach((x, shelfIndex) => {
      box(group, [x, 1.15, -0.56], [0.13, 1.65, 1.34], 0x536c76, { metalness: 0.38 });
      [0.62, 1.12, 1.62].forEach((y) => {
        box(group, [x, y, -0.56], [0.86, 0.055, 1.3], 0x677e85, { metalness: 0.28 });
        [-0.35, 0.34].forEach((z, boxIndex) => {
          box(group, [x + (shelfIndex ? -0.16 : 0.16), y + 0.2, z - 0.52], [0.36, 0.35, 0.38], (shelfIndex + boxIndex) % 2 ? 0xc89762 : 0xd7b581);
        });
      });
    });
    box(group, [0, 0.57, 0.08], [1.3, 0.1, 0.62], 0x9a7658);
    // Laptop, removable USB drive, and a named workstation make the endpoint
    // incident readable in the cutaway view instead of relying on a log only.
    box(group, [0.3, 0.68, 0.1], [0.48, 0.035, 0.32], 0xb9c6c9, { metalness: 0.42 });
    box(group, [0.3, 0.88, -0.035], [0.46, 0.37, 0.035], 0x273a4b, { metalness: 0.25 });
    laptopScreen = box(group, [0.3, 0.88, -0.012], [0.39, 0.29, 0.012], 0x76cdd5, { emissive: 0x2b9fb0, emissiveIntensity: 0.3 });
    usbDrive = new Group();
    const usbBody = box(usbDrive, [0, 0, 0], [0.2, 0.07, 0.085], 0xc63f50, { metalness: 0.28, emissive: 0x701a28, emissiveIntensity: 0.3 });
    usbBody.rotation.z = -0.15;
    box(usbDrive, [0.115, 0, 0], [0.07, 0.045, 0.055], 0xb8c1c5, { metalness: 0.76 });
    usbDrive.position.set(0.03, 0.77, 0.16);
    usbDrive.visible = false;
    group.add(usbDrive);
    activityLabel = labelSprite("USB LẠ · LAPTOP WS-FIN-02", 0xff5966);
    activityLabel.scale.set(2.35, 0.48, 1);
    activityLabel.position.set(0.2, 1.65, 0.04);
    activityLabel.visible = false;
    group.add(activityLabel);
    resolvedActivityLabel = labelSprite("USB ĐÃ CÁCH LY · AGENT", 0x34d399);
    resolvedActivityLabel.scale.set(2.35, 0.48, 1);
    resolvedActivityLabel.position.set(0.2, 1.65, 0.04);
    resolvedActivityLabel.visible = false;
    group.add(resolvedActivityLabel);
    activityWorker = makePerson(group, -0.65, 0.76, 0.72);
  } else {
    // Secure operations floor with server cabinets, status lights and SOC desk.
    [-1.12, 0, 1.12].forEach((x, rackIndex) => {
      box(group, [x, 1.22, -0.5], [0.72, 1.62, 0.92], 0x293b50, { metalness: 0.48, roughness: 0.38 });
      box(group, [x, 1.22, -0.018], [0.58, 1.43, 0.035], 0x1c2b3b, { metalness: 0.3 });
      for (let row = 0; row < 5; row += 1) {
        box(group, [x, 0.67 + row * 0.25, 0.012], [0.43, 0.08, 0.035], 0x415669);
        const led = new Mesh(new SphereGeometry(0.035, 8, 8), material(rackIndex === 1 && row === 2 ? 0xffb777 : 0x53e2c1, { emissive: rackIndex === 1 && row === 2 ? 0xff875a : 0x53e2c1, emissiveIntensity: 0.9 }));
        led.position.set(x + 0.21, 0.68 + row * 0.25, 0.038);
        group.add(led);
      }
    });
    box(group, [0, 0.57, 0.84], [1.65, 0.1, 0.5], 0x33475a);
    box(group, [0, 0.99, 0.67], [1.32, 0.7, 0.08], 0x24364a, { metalness: 0.26 });
    box(group, [0, 1, 0.714], [1.17, 0.55, 0.025], 0x69c5d2, { emissive: 0x207e92, emissiveIntensity: 0.36 });
    const text = labelSprite("SOC · ASSET MONITOR", 0xc4b5ff);
    text.scale.set(1.08, 0.24, 1);
    text.position.set(0, 1.01, 0.735);
    group.add(text);
    makePerson(group, -1.62, 0.64, 0.68);
    // A second employee at the application workstation is animated for
    // unauthorized-software installation drills.
    box(group, [-0.35, 0.57, 0.82], [1.42, 0.1, 0.54], 0x526779);
    box(group, [-0.3, 0.94, 0.61], [0.88, 0.62, 0.06], 0x263b50, { metalness: 0.22 });
    laptopScreen = box(group, [-0.3, 0.94, 0.648], [0.77, 0.49, 0.016], 0x69c5d2, { emissive: 0x207e92, emissiveIntensity: 0.3 });
    activityWorker = makePerson(group, -1.12, 0.72, 0.68);
    activityLabel = labelSprite("ĐANG CÀI ỨNG DỤNG LẠ", 0xc084fc);
    activityLabel.scale.set(2.2, 0.46, 1);
    activityLabel.position.set(-0.25, 1.75, 0.62);
    activityLabel.visible = false;
    group.add(activityLabel);
    resolvedActivityLabel = labelSprite("ỨNG DỤNG ĐÃ CHẶN · AGENT", 0x34d399);
    resolvedActivityLabel.scale.set(2.2, 0.46, 1);
    resolvedActivityLabel.position.set(-0.25, 1.75, 0.62);
    resolvedActivityLabel.visible = false;
    group.add(resolvedActivityLabel);
  }
  return { group, accent: accentMaterial, canopy, focusLight, activityWorker, laptopScreen, usbDrive, activityLabel, resolvedActivityLabel };
}

function makeAgent(scene) {
  const agent = new Group();
  const orange = material(0xff965d, { metalness: 0.12 });
  const ivory = material(0xfff5e9, { metalness: 0.12 });
  const dark = material(0x3c5265, { roughness: 0.42 });
  const body = new Mesh(new CapsuleGeometry(0.28, 0.34, 5, 10), orange);
  body.position.y = 0.52;
  body.castShadow = true;
  agent.add(body);
  const head = new Mesh(new SphereGeometry(0.37, 20, 16), ivory);
  head.position.y = 1.14;
  head.castShadow = true;
  agent.add(head);
  const face = new Mesh(new BoxGeometry(0.48, 0.24, 0.15), dark);
  face.position.set(0, 1.15, 0.28);
  agent.add(face);
  [-0.11, 0.11].forEach((x) => {
    const eye = new Mesh(new SphereGeometry(0.045, 8, 8), material(0xffffff, { emissive: 0xffffff, emissiveIntensity: 0.45 }));
    eye.position.set(x, 1.18, 0.37);
    agent.add(eye);
  });
  const antenna = new Mesh(new CylinderGeometry(0.025, 0.025, 0.2, 8), material(0xa7b1b8));
  antenna.position.y = 1.53;
  agent.add(antenna);
  const beacon = new Mesh(new SphereGeometry(0.07, 10, 10), material(0xffd178, { emissive: 0xffaa42, emissiveIntensity: 1.1 }));
  beacon.position.y = 1.65;
  agent.add(beacon);
  const ring = new Mesh(new TorusGeometry(0.58, 0.035, 8, 48), new MeshBasicMaterial({ color: 0xffe5ac, transparent: true, opacity: 0.72 }));
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.14;
  agent.add(ring);
  scene.add(agent);
  return { agent, ring };
}

function makeTree(scene, x, z, scale = 1) {
  const trunk = new Mesh(new CylinderGeometry(0.11 * scale, 0.16 * scale, 0.72 * scale, 8), material(0x805943));
  trunk.position.set(x, 0.38 * scale, z);
  trunk.castShadow = true;
  scene.add(trunk);
  const crown = new Mesh(new SphereGeometry(0.62 * scale, 12, 10), material(0x68896b, { roughness: 1 }));
  crown.position.set(x, 0.95 * scale, z);
  crown.castShadow = true;
  scene.add(crown);
}

function makeVehicle(scene, x, z, color, truck = false) {
  const vehicle = new Group();
  vehicle.position.set(x, 0.13, z);
  const paint = material(color, { metalness: 0.24, roughness: 0.48 });
  box(vehicle, [0, 0.25, 0], truck ? [2.35, 0.48, 0.82] : [1.45, 0.36, 0.72], truck ? 0xece8df : color, { metalness: 0.12 });
  box(vehicle, truck ? [0.78, 0.55, 0] : [-0.04, 0.51, 0], truck ? [0.72, 0.56, 0.78] : [0.72, 0.34, 0.62], truck ? color : 0xa9d8e2, { transparent: !truck, opacity: 0.8 });
  const wheels = truck ? [-0.7, 0.75] : [-0.45, 0.45];
  wheels.forEach((wheelX) => [-0.35, 0.35].forEach((wheelZ) => {
    const wheel = new Mesh(new CylinderGeometry(0.17, 0.17, 0.12, 12), material(0x24313e));
    wheel.rotation.x = Math.PI / 2;
    wheel.position.set(wheelX, 0.17, wheelZ);
    vehicle.add(wheel);
  }));
  const light = new Mesh(new BoxGeometry(0.12, 0.12, 0.12), material(0xffe6a6, { emissive: 0xffca63, emissiveIntensity: 0.25 }));
  light.position.set(truck ? 1.19 : 0.72, 0.31, 0.23);
  vehicle.add(light);
  vehicle.userData.paint = paint;
  scene.add(vehicle);
}

function addCampus(scene) {
  box(scene, [0, 0.105, 4.75], [18.4, 0.16, 1.65], 0x38444b, { roughness: 0.96 });
  for (let x = -8; x <= 8; x += 1.25) box(scene, [x, 0.195, 4.75], [0.58, 0.012, 0.035], 0xd6cba9);
  box(scene, [-5.15, 0.2, 3.35], [3.2, 0.035, 1.22], 0x777d76);
  [-6.58, -5.5, -4.42, -3.34].forEach((x) => box(scene, [x, 0.225, 3.35], [0.035, 0.014, 1.02], 0xe8e0c8));
  box(scene, [0, 0.12, -6.05], [18, 0.12, 0.54], 0x777d76);
  [-8.2, 8.2].forEach((x) => box(scene, [x, 0.19, 0], [0.11, 0.12, 10.5], 0xc8c3b4));
  box(scene, [0, 0.72, 5.65], [0.3, 1.3, 0.3], 0x536b78);
  box(scene, [5.8, 0.72, 5.65], [0.3, 1.3, 0.3], 0x536b78);
  box(scene, [2.9, 1.3, 5.65], [6.1, 0.22, 0.34], 0x33485a);
  const campusSign = labelSprite("VIỆT TÍN LOGISTICS · CAMPUS", 0xffb777);
  campusSign.scale.set(3.6, 0.75, 1);
  campusSign.position.set(2.9, 1.32, 5.46);
  scene.add(campusSign);
  makeVehicle(scene, -5.55, 3.38, 0x6f8dae, false);
  makeVehicle(scene, 7.25, 4.72, 0xe8844f, true);
  [[-9.2, -4.7, 0.75], [-9, 2.4, 0.62], [9.1, -4.7, 0.72], [9.15, 1.1, 0.55], [2.8, -6.05, 0.65]].forEach(([x, z, scale]) => makeTree(scene, x, z, scale));
}

export default function EnterpriseScene3D({ room, visited, selected, working, resolved, currentTool, currentStep, activity }) {
  const hostRef = useRef(null);
  const liveState = useRef({ room, working, activity });
  liveState.current = { room, working, activity };

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return undefined;
    const scene = new Scene();
    scene.background = new Color(0xc7d8dc);
    scene.fog = new Fog(0xc7d8dc, 25, 48);
    const camera = new PerspectiveCamera(38, 1, 0.1, 100);
    camera.position.set(12, 11, 17);
    const renderer = new WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = PCFSoftShadowMap;
    renderer.outputColorSpace = SRGBColorSpace;
    renderer.toneMapping = ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.18;
    renderer.domElement.setAttribute("aria-label", "Mô hình 3D tương tác của doanh nghiệp giả lập");
    renderer.domElement.setAttribute("role", "img");
    host.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0.7, -0.25);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 10;
    controls.maxDistance = 27;
    controls.maxPolarAngle = Math.PI * 0.47;
    scene.add(new HemisphereLight(0xf1f8ff, 0x825d4c, 2.0));
    const sun = new DirectionalLight(0xffe7ca, 3.2);
    sun.position.set(-7, 15, 8);
    sun.castShadow = true;
    sun.shadow.mapSize.set(1024, 1024);
    scene.add(sun);
    const fill = new DirectionalLight(0x9bc9ff, 1.15);
    fill.position.set(9, 8, -8);
    scene.add(fill);

    const ground = new Mesh(new PlaneGeometry(34, 25), material(0x738971, { roughness: 1 }));
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.08;
    ground.receiveShadow = true;
    scene.add(ground);
    const grid = new GridHelper(34, 34, 0xc6d0bd, 0x889b87);
    grid.position.y = -0.055;
    grid.material.transparent = true;
    grid.material.opacity = 0.055;
    scene.add(grid);
    box(scene, [0, 0.03, 0], [20, 0.12, 11.8], 0xc7c3b5, { roughness: 0.94 });
    [-8.7, 8.7].forEach((x) => box(scene, [x, 0.1, 0], [0.14, 0.18, 10.2], 0xd0c7b2));
    const route = new Line(new BufferGeometry().setFromPoints([
      new Vector3(-5.1, 0.12, 2.1), new Vector3(-3, 0.12, 4.15),
      new Vector3(0, 0.12, 3.6), new Vector3(2.7, 0.12, 3.9),
      new Vector3(5.1, 0.12, 2.1),
    ]), new LineDashedMaterial({ color: 0xfff3d6, dashSize: 0.35, gapSize: 0.24, transparent: true, opacity: 0.88 }));
    route.computeLineDistances();
    scene.add(route);
    addCampus(scene);

    const areaObjects = Object.fromEntries(Object.entries(AREAS).map(([key, area]) => [key, buildArea(scene, key, area)]));
    const marker = new Group();
    const markerRing = new Mesh(new TorusGeometry(0.7, 0.045, 8, 48), new MeshBasicMaterial({ color: 0xff4e5e, transparent: true, opacity: 0.85 }));
    markerRing.rotation.x = Math.PI / 2;
    markerRing.position.y = 0.16;
    const markerCore = new Mesh(new OctahedronGeometry(0.23, 0), material(0xff4e5e, { emissive: 0xff263e, emissiveIntensity: 1.0 }));
    markerCore.position.y = 0.85;
    marker.add(markerRing, markerCore);
    scene.add(marker);
    const { agent, ring } = makeAgent(scene);

    let frame = 0;
    let width = 1;
    let height = 1;
    const resize = () => {
      width = Math.max(host.clientWidth, 1);
      height = Math.max(host.clientHeight, 1);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();
    const clock = new Clock();
    const animate = () => {
      frame = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      const { room: activeRoom, working: isWorking, activity: incidentActivity } = liveState.current;
      const targetArea = AREAS[activeRoom] || null;
      const agentTarget = targetArea
        ? new Vector3(targetArea.position[0], 0, targetArea.position[2] + 2.35)
        : new Vector3(0, 0, 4.3);
      agent.position.lerp(agentTarget, 0.045);
      agent.position.y = 0.09 + Math.sin(t * 2.5) * 0.08;
      ring.rotation.z = t * 0.7;
      markerCore.rotation.y = t * 0.8;
      marker.position.y = 0.035 + Math.sin(t * 2.8) * 0.08;
      if (targetArea) {
        marker.position.x = targetArea.position[0] + 1.2;
        marker.position.z = targetArea.position[2] + 0.85;
      } else {
        marker.position.x = 0;
        marker.position.z = -0.3;
      }
      Object.entries(areaObjects).forEach(([key, item]) => {
        const active = key === activeRoom;
        item.canopy.material.opacity = active ? 0.34 : 0.13;
        item.accent.emissiveIntensity = active ? 0.58 : 0.16;
        item.focusLight.intensity = active ? 1.0 : 0.25;
        item.group.scale.y = active && isWorking ? 1 + Math.sin(t * 3.4) * 0.012 : 1;
        const usbIncident = key === "hardware" && incidentActivity?.type === "unapproved_usb_inserted";
        const softwareIncident = key === "software" && incidentActivity?.type === "unapproved_software_installed";
        const showingActivity = usbIncident || softwareIncident;
        if (item.activityWorker) {
          const home = key === "hardware" ? [-0.65, 0.76] : [-1.12, 0.72];
          const workingPosition = key === "hardware" ? [-0.15, 0.36] : [-0.72, 0.96];
          const destination = showingActivity ? workingPosition : home;
          item.activityWorker.position.x += (destination[0] - item.activityWorker.position.x) * 0.035;
          item.activityWorker.position.z += (destination[1] - item.activityWorker.position.z) * 0.035;
          item.activityWorker.rotation.y = showingActivity ? -0.35 : 0;
          const arms = item.activityWorker.userData.actionArms || [];
          arms.forEach((arm, index) => {
            const side = index === 0 ? -1 : 1;
            arm.rotation.z = showingActivity
              ? side * (-0.72 + Math.sin(t * 7) * 0.08)
              : side * -0.38;
          });
        }
        if (item.usbDrive) {
          item.usbDrive.visible = usbIncident && incidentActivity?.phase !== "contained";
          item.usbDrive.position.y = 0.77 + (usbIncident && incidentActivity?.phase !== "contained" ? Math.sin(t * 5) * 0.025 : 0);
        }
        if (item.laptopScreen) {
          const unsafeColor = usbIncident ? 0xff5966 : 0xc084fc;
          item.laptopScreen.material.color.setHex(showingActivity ? unsafeColor : key === "software" ? 0x69c5d2 : 0x76cdd5);
          item.laptopScreen.material.emissive?.setHex(showingActivity ? unsafeColor : 0x207e92);
          item.laptopScreen.material.emissiveIntensity = showingActivity ? 0.58 : 0.3;
        }
        if (item.activityLabel) item.activityLabel.visible = showingActivity && incidentActivity?.phase !== "contained";
        if (item.resolvedActivityLabel) item.resolvedActivityLabel.visible = showingActivity && incidentActivity?.phase === "contained";
      });
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      scene.traverse((object) => {
        object.geometry?.dispose();
        if (Array.isArray(object.material)) object.material.forEach((entry) => entry.dispose());
        else object.material?.dispose();
        object.material?.map?.dispose();
      });
      renderer.dispose();
      host.removeChild(renderer.domElement);
    };
  }, []);

  const area = AREAS[room];
  const position = area?.position || [0, 0, -0.25];
  return <div className="relative h-[500px] overflow-hidden rounded-[30px] border-2 border-[#f3bd91]/70 bg-[#b9d5e2] shadow-2xl md:h-[580px]">
    <div ref={hostRef} className="absolute inset-0" />
    <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-full bg-[#fff9ee]/95 px-4 py-2 text-xs font-black text-[#71513e] shadow">🏢 VIỆT TÍN LOGISTICS · DOANH NGHIỆP GIẢ LẬP</div>
    {activity&&<div aria-live="polite" className={`pointer-events-none absolute left-4 top-[58px] z-10 rounded-xl border px-3 py-2 text-[9px] font-black shadow-lg ${activity.phase==="contained"?"border-emerald-300/40 bg-emerald-950/90 text-emerald-100":"border-rose-300/40 bg-rose-950/90 text-rose-100"}`}>
      {activity.phase==="contained"?"AGENT ĐÃ CÔ LẬP / CHẶN TÌNH HUỐNG":activity.phase==="agent_check"?"AGENT ĐANG KIỂM TRA THIẾT BỊ":activity.type==="unapproved_usb_inserted"?"MÔ PHỎNG: NHÂN VIÊN CẮM USB LẠ VÀO LAPTOP":"MÔ PHỎNG: NHÂN VIÊN ĐANG CÀI APP LẠ"}
      {activity.employee_id&&<span className="ml-2 font-mono text-white/70">{activity.employee_id} · {activity.asset_id}{activity.accessory_id?` · ${activity.accessory_id}`:""}</span>}
      {activity.source==="issue_description"&&<span className="ml-2 font-normal text-white/60">(minh họa theo mô tả)</span>}
    </div>}
    {selected&&<div className="pointer-events-none absolute right-4 top-4 z-10 rounded-xl border border-white/40 bg-[#172337]/90 px-3 py-2 text-right shadow-lg"><div className="text-[9px] font-black uppercase tracking-wider text-[#ffca91]">Đối tượng Agent đang kiểm tra</div><div className="mt-1 max-w-52 truncate font-mono text-xs font-bold text-white">{selected.target.asset_id}</div><div className="max-w-52 truncate text-[10px] text-slate-300">{selected.human_context?.employee_id} · {selected.department}</div></div>}
    <div className="pointer-events-none absolute bottom-[78px] left-4 rounded-xl border border-white/30 bg-[#172337]/85 px-3 py-2 text-[9px] font-bold text-white/90 shadow">{room === "hub" ? "GÓC NHÌN TỔNG THỂ" : `${area?.title} · ${selected?.control_id || "KHU VỰC DOANH NGHIỆP"}`}{selected&&<span className="ml-2 text-[#ffca91]">{selected.target.name}</span>}</div>
    <div className="pointer-events-none absolute bottom-4 left-4 rounded-2xl border border-white/50 bg-[#fff9ed]/95 px-4 py-3 text-[#604a3b] shadow-lg">
      <p className="text-[10px] font-black uppercase tracking-widest">Agent đang thực hiện</p>
      <p className="mt-1 text-sm font-black">{currentStep || (working ? "Đang tiếp nhận sự cố" : "Chờ chọn kịch bản")}</p>
      {currentTool&&<p className="mt-1 text-[10px] font-bold text-violet-700">TOOL · {currentTool}</p>}
    </div>
    <div className="pointer-events-none absolute bottom-4 right-4 flex items-center gap-2 rounded-full bg-[#1c2b3d]/90 px-3 py-2 text-[10px] font-bold text-emerald-200"><span className={`h-2 w-2 rounded-full ${working?"animate-pulse bg-emerald-300":"bg-slate-400"}`}/>{working ? "LIVE AGENT TRACE" : resolved ? "ĐÃ XÁC MINH" : "KÉO ĐỂ XOAY · LĂN ĐỂ THU PHÓNG"}</div>
    <div className="pointer-events-none absolute bottom-[72px] right-4 rounded-lg bg-[#172337]/75 px-2 py-1 text-[8px] text-white/70">{visited.length}/3 KHU ĐÃ KIỂM TRA</div>
  </div>;
}
