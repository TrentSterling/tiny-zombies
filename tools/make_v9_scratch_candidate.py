#!/usr/bin/env python3
"""Reproduce the bounded-scratch diagnostic candidate; never overwrite the source.

Usage: python make_v9_scratch_candidate.py [original.html] [candidate.html]
Requires Node.js for the JavaScript syntax and shader-extraction checks.
No browser or GPU execution is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ORIGINAL_SHA256 = "787cdb9b13b91e27313e550826580e4030ce314fb571299ec171ddf051f99349"
CANDIDATE_SHA256 = "1be63cbf1a3887251b0b26067133e71068f7c820c96f5f1c28a9b8718c72f6df"
PATCHES = [
    ("magazine_scalar_parameter", 1,
     "fn magazineSize(s:State)->f32 {return 120.0+s.modsA.y*30.0;}",
     "fn magazineSize(magazineUpgrade:f32)->f32 {return 120.0+magazineUpgrade*30.0;}"),
    ("reload_scalar_parameter", 1,
     "fn reloadDuration(s:State)->f32 {return max(.85,1.65-s.modsA.x*.22);}",
     "fn reloadDuration(reloadUpgrade:f32)->f32 {return max(.85,1.65-reloadUpgrade*.22);}"),
    ("magazine_scalar_call_sites", 3, "magazineSize(S)", "magazineSize(S.modsA.y)"),
    ("reload_scalar_call_site", 1, "reloadDuration(S)", "reloadDuration(S.modsA.x)"),
    ("fracture_workgroup_scratch", 1,
     "var<private> supported8:array<u32,512>;\nvar<private> queue8:array<u32,512>;",
     "// Scratch is shared by this single-invocation workgroup: 4096 bytes.\nvar<workgroup> supported8:array<u32,512>;\nvar<workgroup> queue8:array<u32,512>;"),
    ("goap_workgroup_scratch", 1,
     "fn goap7(a0:Buddy7,initial:u32,goal:u32,dist:f32)->Buddy7 {\n var a=a0;var costs:array<f32,128>;var codes:array<u32,128>;var lens:array<u32,128>;var closed:array<u32,128>;",
     "// One invocation plans the three buddies sequentially; each call initializes all 2048 scratch bytes.\nvar<workgroup> costs:array<f32,128>;\nvar<workgroup> codes:array<u32,128>;\nvar<workgroup> lens:array<u32,128>;\nvar<workgroup> closed:array<u32,128>;\nfn goap7(a0:Buddy7,initial:u32,goal:u32,dist:f32)->Buddy7 {\n var a=a0;"),
    ("astar_workgroup_scratch", 1,
     "struct Node7{cell:vec2i, parent:i32, used:u32, g:f32, f:f32, pad:vec2f};\n@compute",
     "struct Node7{cell:vec2i, parent:i32, used:u32, g:f32, f:f32, pad:vec2f};\n// Each one-invocation A* workgroup owns a separate 9216-byte scratch region.\nvar<workgroup> nodes:array<Node7,256>;\nvar<workgroup> reverse:array<vec2i,128>;\n@compute"),
    ("remove_astar_local_nodes", 1,
     " var nodes:array<Node7,256>;var n=1u;", " var n=1u;"),
    ("remove_astar_local_reverse", 1,
     " var reverse:array<vec2i,128>;var num=0u;", " var num=0u;"),
]

NODE_CHECK = r"""
const fs=require('fs'),vm=require('vm');
function extract(path){
 const html=fs.readFileSync(path,'utf8');
 let js=html.slice(html.indexOf('<script>')+8,html.lastIndexOf('</script>'));
 if(js.split('main().catch(fail);').length!==2)throw Error('Unexpected main invocation');
 js=js.replace('main().catch(fail);','');
 const c={console,URLSearchParams,location:{search:''},document:{getElementById(){return {}}},addEventListener(){},atob:s=>Buffer.from(s,'base64').toString('binary')};
 c.window=c;vm.createContext(c);vm.runInContext(js,c);return c.__TINY_SOURCES__;
}
const base=extract(process.argv[1]),candidate=extract(process.argv[2]);
if(Object.keys(candidate).length!==40)throw Error('Expected 40 shader modules');
for(const source of Object.values(candidate))if(/fn\s+\w+\([^)]*:\s*State/.test(source))throw Error('State-valued function parameter remains');
const scratch={fracture8:['supported8','queue8'],buddy:['costs','codes','lens','closed'],squadNav7:['nodes','reverse']};
for(const [name,names]of Object.entries(scratch)){
 if(!/@compute\s+@workgroup_size\(1\)/.test(candidate[name]))throw Error('Not single invocation: '+name);
 for(const v of names){
  if((candidate[name].match(new RegExp('var<workgroup> '+v+':','g'))||[]).length!==1)throw Error('Workgroup declaration count: '+name+':'+v);
  if(new RegExp('var(?:<private>)? '+v+':').test(candidate[name]))throw Error('Private scratch remains: '+name+':'+v);
 }
}
for(const name of ['render','post','ui']){
 const normalized=candidate[name]
  .replace('fn magazineSize(magazineUpgrade:f32)->f32 {return 120.0+magazineUpgrade*30.0;}','fn magazineSize(s:State)->f32 {return 120.0+s.modsA.y*30.0;}')
  .replace('fn reloadDuration(reloadUpgrade:f32)->f32 {return max(.85,1.65-reloadUpgrade*.22);}','fn reloadDuration(s:State)->f32 {return max(.85,1.65-s.modsA.x*.22);}');
 if(normalized!==base[name])throw Error('Unexpected renderer change: '+name);
}
console.log(JSON.stringify({shader_modules_extracted:40,single_invocation_kernels:true,workgroup_array_declarations:8,private_scratch_duplicates:0,state_valued_helper_parameters:0,renderer_unchanged_except_unused_scalar_helpers:true}));
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=folder / "tiny_zombies_v9.html")
    parser.add_argument("output", nargs="?", type=Path, default=folder / "v9-scratch-candidate.html")
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    assert source != output, "Refusing to overwrite original"
    original_bytes = source.read_bytes()
    assert digest(original_bytes) == ORIGINAL_SHA256, "Original hash mismatch; refusing to patch"
    text = original_bytes.decode("utf-8")
    replacements = {}
    for name, expected, old, new in PATCHES:
        found = text.count(old)
        assert found == expected, f"{name}: expected {expected} exact matches, found {found}"
        text = text.replace(old, new)
        replacements[name] = found
    result = text.encode("utf-8")
    assert digest(result) == CANDIDATE_SHA256, "Candidate hash mismatch"
    if output.exists():
        assert output.read_bytes() == result, "Refusing to overwrite a different candidate"
    else:
        output.write_bytes(result)
    assert source.read_bytes() == original_bytes, "Original unexpectedly changed"
    script = text.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    subprocess.run(["node", "--check"], input=script, text=True, check=True, capture_output=True)
    extracted = subprocess.run(["node", "-e", NODE_CHECK, str(source), str(output)], text=True,
                               check=True, capture_output=True)
    structural = json.loads(extracted.stdout)
    footprints = {"fracture8": 2 * 512 * 4, "buddy": 4 * 128 * 4,
                  "squadNav7": 256 * 32 + 128 * 8}
    assert all(n <= 16384 for n in footprints.values())
    report = {
        "purpose": "Diagnostic candidate; no GPU execution or confirmed crash fix claimed",
        "original": {"file": source.name, "sha256": ORIGINAL_SHA256, "preserved": True},
        "candidate": {"file": output.name, "sha256": CANDIDATE_SHA256, "bytes": len(result)},
        "exact_replacement_counts": replacements,
        "javascript_syntax": "passed",
        "structural_checks": structural,
        "source_layout_bytes": {"State": 8880, "Buddy7": 512, "Wreck8": 336, "Node7": 32},
        "workgroup_scratch_bytes": footprints,
        "workgroup_baseline_limit_bytes": 16384,
        "bindings_changed": False,
        "dispatches_changed": False,
        "gpu_compilation": "not run by this script",
        "gpu_execution": "not run by this script",
        "caveats": [
            "Memory sizes are WGSL source layouts, not measured NVIDIA compiler spills.",
            "Scratch equivalence relies on workgroup_size(1); larger groups need ownership and synchronization changes.",
            "GOAP resets every scratch element per call; fracture and A* read only entries initialized by that invocation."
        ]
    }
    report_path = output.with_name(output.stem + "-structural-check.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": str(output), "checks": str(report_path), "sha256": digest(result)}))


if __name__ == "__main__":
    main()
