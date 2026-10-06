// Tests real serialization/validation functions without writing reviewer drafts.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('src/paired_review.js','utf8');
const definition=JSON.parse(fs.readFileSync('work/slr86/paired-ai-001/review_form_definition.json','utf8'));
const sections=new Map();
function section(duration,ai){const ratings=ai?Object.keys(definition.rating_options).map(k=>({dataset:{rating:k},value:''})):[];const notes={value:''};return {dataset:{duration:String(duration),updated:'2026-10-03T00:00:00Z'},ratings,notes,intervals:[],tags:[],querySelectorAll(s){return s==='[data-rating]'?ratings:s==='[data-tag]:checked'?this.tags:this.intervals;},querySelector(){return notes;},closest(){return {dataset:{sentence:'p01'}}}};}
for(const s of definition.items){const natural=section(s.natural_duration_s,false);const ais=new Map(s.ai_generations.map(g=>[g.ai_generation_id,section(g.duration_s,true)]));sections.set(s.sentence_id,{natural,ais,querySelector(sel){return sel==='.natural'?natural:ais.get(sel.match(/data-generation="([^"]+)"/)[1]);}});}
const reviewer={value:'test-reviewer'};
const context={definition,document:{getElementById(){return reviewer;},querySelector(sel){return sections.get(sel.match(/data-sentence="([^"]+)"/)[1]);}},Date,Number,Error};vm.createContext(context);vm.runInContext(source.slice(source.indexOf('function readSection'),source.indexOf('function save')),context);
let p=JSON.parse(JSON.stringify(context.payload(true)));assert.equal(p.items.length,6);assert.equal(p.items.flatMap(s=>s.ai_annotations).length,12);assert.equal(p.items[0].ai_annotations[0].ratings.lexical_tone_realization,null);assert.equal(p.items[0].ai_annotations[0].annotation_timestamp,null);assert.equal(p.items[0].exact_yoruba_text,definition.items[0].exact_text);
const a=sections.get('p01').ais.get('p01_coral_r01');a.ratings[0].value='cannot determine';a.notes.value='Test ẹ / ọ / ṣ';
p=JSON.parse(JSON.stringify(context.payload(true)));assert.equal(p.items[0].ai_annotations[0].ratings.lexical_tone_realization,'cannot determine');assert.equal(p.items[0].ai_annotations[1].ratings.lexical_tone_realization,null);assert.equal(p.items[0].ai_annotations[0].notes,'Test ẹ / ọ / ṣ');assert.equal(p.items[0].ai_annotations[0].reviewer_identifier,'test-reviewer');assert.equal(p.items[0].ai_annotations[0].model_snapshot,'gpt-4o-mini-tts-2025-12-15');assert.ok(p.items[0].ai_annotations[0].annotation_timestamp);assert.equal(p.dimensions_combined,false);
const interval=(start,end)=>({querySelector(sel){return {value:sel==='.start'?start:sel==='.end'?end:'interval note'};}});
a.intervals=[interval('0.1','0.5')];assert.equal(context.payload(true).items[0].ai_annotations[0].problematic_time_intervals[0].start_s,.1);
for(const pair of [['',''],['1','0.5'],['-1','1'],['0','999']]){a.intervals=[interval(...pair)];assert.throws(()=>context.payload(true),/Invalid interval/);}
a.intervals=[];reviewer.value='';assert.throws(()=>context.payload(true),/reviewer identifier/);
console.log('PASS: blank/null defaults; 12 independent annotations; exact metadata/diacritics; timestamp; interval bounds; reviewer required; no combined score.');
