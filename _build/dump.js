// Evaluate each source page's renderVals() for the states we need, dump JSON.
const fs = require('fs');
const dir = process.argv[2];
function load(file) {
  const src = fs.readFileSync(dir + '/' + file, 'utf8');
  const m = src.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/);
  const DCLogic = class { constructor(p) { this.props = p || {}; this.state = {}; } setState(s) { Object.assign(this.state, s); } };
  const Component = new Function('DCLogic', m[1] + '\nreturn Component;')(DCLogic);
  return Component;
}
function strip(o) { return JSON.parse(JSON.stringify(o)); }
function run(file, states) {
  const C = load(file);
  const out = {};
  for (const [k, st] of Object.entries(states)) {
    const c = new C({});
    Object.assign(c.state, st);
    out[k] = strip(c.renderVals());
  }
  return out;
}
const res = {
  fork: run('Fork.dc.html', { none: { route: null }, local: { route: 'local' }, main: { route: 'main' } }),
  main: run('Main.dc.html', {
    none: {}, reels: { pick: 'reels' }, app: { pick: 'app' }, flow: { pick: 'flow' }, unsure: { pick: 'unsure' },
    tab_app: { tab: 'app' }, tab_method: { tab: 'method' }, closed: { open: -1 }
  }),
  mainframe: run('Mainframe.dc.html', {
    none: {}, fraction: { reading: 'fraction' }, ex_c: { ex: 'c' }, ex_d: { ex: 'd' }, closed: { open: -1 }
  })
};
fs.writeFileSync(process.argv[3], JSON.stringify(res, null, 1));
console.log('ok');
