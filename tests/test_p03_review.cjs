const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('src/p03_interval_review.js','utf8');
const helpers=source.slice(source.indexOf('const median='),source.indexOf('function save()'));
const context=vm.createContext({});vm.runInContext(helpers,context);
const p=JSON.parse(fs.readFileSync('work/slr86/p03-supervised-001/annotation_package.json','utf8'));
for(const r of p.records){context.r=r;context.s=r.segments[0];vm.runInContext('validate(r)',context);const m=vm.runInContext('measurements(r,s)',context);assert(m.frames.every(f=>f.timestamp_s>=context.s.start_s&&f.timestamp_s<context.s.end_s));assert(m.summary.window_crossing_frames>=0);assert(m.summary.screened_contained_frames<=m.summary.total_frames);}
context.r={duration_s:1,segments:[{start_s:.4,end_s:.2}]};assert.throws(()=>vm.runInContext('validate(r)',context));
context.r={duration_s:1,segments:[{start_s:0,end_s:1,boundary_review:'confirmed',written_unit:'kò',confidence:''}]};assert.throws(()=>vm.runInContext('validate(r)',context));
console.log('PASS: JS window assignment, reliability, invalid boundary and confirmation checks');
