// Room-local coordinates; obstacles already include the avatar's clearance.
export function isWalkable(point, bounds, obstacles) {
  return Number.isFinite(point.x) && Number.isFinite(point.z)
    && point.x >= bounds.minX && point.x <= bounds.maxX
    && point.z >= bounds.minZ && point.z <= bounds.maxZ
    && !obstacles.some(rect => point.x >= rect.minX && point.x <= rect.maxX && point.z >= rect.minZ && point.z <= rect.maxZ);
}

export function findPath(start, goal, bounds, obstacles, step = .4) {
  if (!isWalkable(start, bounds, obstacles) || !isWalkable(goal, bounds, obstacles)) return [];
  const width = Math.floor((bounds.maxX - bounds.minX) / step) + 1;
  const height = Math.floor((bounds.maxZ - bounds.minZ) / step) + 1;
  const position = id => ({x: bounds.minX + (id % width) * step, z: bounds.minZ + Math.floor(id / width) * step});
  const clearSegment = (a, b) => {
    const samples = Math.max(1, Math.ceil(Math.hypot(b.x - a.x, b.z - a.z) / .1));
    for (let i = 0; i <= samples; i++) if (!isWalkable({x: a.x + (b.x - a.x) * i / samples, z: a.z + (b.z - a.z) * i / samples}, bounds, obstacles)) return false;
    return true;
  };
  const nearest = point => {
    let best = null, distance = Infinity;
    const x = Math.round((point.x - bounds.minX) / step), z = Math.round((point.z - bounds.minZ) / step);
    for (let dx = -2; dx <= 2; dx++) for (let dz = -2; dz <= 2; dz++) {
      const cx = x + dx, cz = z + dz;
      if (cx < 0 || cx >= width || cz < 0 || cz >= height) continue;
      const id = cz * width + cx, candidate = position(id), d = Math.hypot(candidate.x - point.x, candidate.z - point.z);
      if (d < distance && clearSegment(point, candidate)) {best = id; distance = d;}
    }
    return best;
  };
  const first = nearest(start), last = nearest(goal);
  if (first === null || last === null) return [];
  const heuristic = id => Math.abs(id % width - last % width) + Math.abs(Math.floor(id / width) - Math.floor(last / width));
  const open = [first], cost = new Map([[first, 0]]), previous = new Map(), closed = new Set();
  while (open.length) {
    open.sort((a, b) => cost.get(a) + heuristic(a) - cost.get(b) - heuristic(b));
    const current = open.shift();
    if (current === last) {
      const path = [position(last)];
      let cursor = last;
      while (previous.has(cursor)) {cursor = previous.get(cursor); path.unshift(position(cursor));}
      path.push({x: goal.x, z: goal.z});
      return path;
    }
    closed.add(current);
    const x = current % width, z = Math.floor(current / width);
    for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nx = x + dx, nz = z + dz, next = nz * width + nx;
      if (nx < 0 || nx >= width || nz < 0 || nz >= height || closed.has(next) || !isWalkable(position(next), bounds, obstacles)) continue;
      if (cost.get(current) + 1 >= (cost.get(next) ?? Infinity)) continue;
      cost.set(next, cost.get(current) + 1); previous.set(next, current);
      if (!open.includes(next)) open.push(next);
    }
  }
  return [];
}
