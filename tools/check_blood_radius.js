'use strict';
// Static/source equivalence only. No browser, WebGPU, or gameplay is executed.
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const [baselinePath,candidatePath]=process.argv.slice(2);
const baseline=fs.readFileSync(baselinePath),candidate=fs.readFileSync(candidatePath);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const old='let radius=select(2,3,q.c.w<.5);',replacement='let radius=select(1,2,q.c.w<.5);';
assert.equal(sha(baseline),'1be63cbf1a3887251b0b26067133e71068f7c820c96f5f1c28a9b8718c72f6df');
assert.equal(baseline.toString().split(old).length,2);
assert.deepEqual(candidate,Buffer.from(baseline.toString().replace(old,replacement)));
function extract(buf){
 const html=buf.toString(),js=html.slice(html.indexOf('<script>')+8,html.lastIndexOf('</script>'));
 new vm.Script(js);
 assert.equal(js.split('main().catch(fail);').length,2);
 const context={console,URLSearchParams,location:{search:''},document:{getElementById(){return {}}},addEventListener(){},atob:s=>Buffer.from(s,'base64').toString('binary')};
 context.window=context;vm.createContext(context);vm.runInContext(js.replace('main().catch(fail);',''),context);
 return context.__TINY_SOURCES__;
}
const before=extract(baseline),after=extract(candidate),changed=Object.keys(before).filter(k=>before[k]!==after[k]);
assert.equal(Object.keys(after).length,40);assert.deepEqual(changed,['integrate']);
assert.equal(after.integrate,before.integrate.replace(old,replacement));
function footprint(radius){
 let cells=0;
 for(let y=-radius;y<=radius;y++)for(let x=-radius;x<=radius;x++)if((x*x+y*y)/(radius*radius+1)<1.25)cells++;
 return {radius_cells:radius,painted_cells:cells,area_m2:cells/64,bounding_width_m:(radius*2+1)/8};
}
const report={baseline_sha256:sha(baseline),candidate_sha256:sha(candidate),candidate_bytes:candidate.length,changed_byte_count:[...baseline].filter((b,i)=>b!==candidate[i]).length,javascript_syntax:'passed',shader_modules:40,changed_shader_modules:changed,only_exact_radius_substitution:true,unchanged:['particle emission and counts','flying particle sizes, velocities, lifetimes and colors','grounding and stamp cadence','floor blood intensity inputs and shading','wall blood and drips','persistent paint storage and timestamps','gameplay and budgets','scratch crash repair','rendering'],isolated_stamp_footprints:{gore:{before:footprint(2),after:footprint(1),reduction_percent:100*(1-9/21)},droplet:{before:footprint(3),after:footprint(2),reduction_percent:100*(1-21/37)}},gpu_compilation:'not run',gpu_execution:'not run',visual_validation:'pending Windows paired capture',caveats:['Areas describe individual non-overlapping paint stamps on an infinite floor. Overlap and world boundaries change combined coverage.','Paint edge falloff remains the same function, scaled by the reduced radius.','Persistent marks can still accumulate into a carpet during long play. No cap, fading, alpha, frequency, or cleanup change is included.']};
console.log(JSON.stringify(report,null,2));
