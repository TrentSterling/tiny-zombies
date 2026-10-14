# Tiny Zombies: No One Left

A standalone WebGPU voxel zombie game. This is the 2026 V9 prototype, distinct from the 2015 Unity experiment.

## Play locally

Serve this directory over localhost, for example `python -m http.server 8000`, and open `http://localhost:8000/` in a WebGPU-capable desktop browser with hardware acceleration. Public hosting requires HTTPS. No package installation, build step, external libraries, network assets, or WebGL fallback is required.

Click to start. Move with WASD or arrow keys; aim with the mouse and left-click to fire. Space throws a grenade, Shift dashes, mouse wheel zooms, Escape pauses, Backspace restarts, M mutes, and T toggles demo mode. F3 shows statistics and F2 exports diagnostics.

## V9 compatibility repair

The release HTML preserves the uploaded V9 gameplay and quiet centered HUD. A narrow shader change moves bounded fracture, squad-navigation and buddy-planning scratch arrays into workgroup storage. Those kernels use one invocation per workgroup. Two helper functions now receive scalar upgrade values instead of copying the full state struct. Entity limits and gameplay budgets are unchanged.

The original reproduced a GPU device hang on an NVIDIA RTX 5070 Ti with Chrome 155 and driver 591.86. The repair passed the same previously failing active simulation/render frame. The repaired build also passed a bounded 60-second hardware gameplay test. This is evidence on the tested configuration, not a guarantee for every browser or GPU.

## Smaller floor blood stamps

At the owner's request, the ground-stamp radius is now 2 paint cells for droplets and 1 for gore, previously 3 and 2. Isolated painted areas shrink from 37 to 21 cells and 21 to 9 cells. Particle counts, flight, colors, wall marks, impact intensity and persistence remain unchanged. Long sessions can still accumulate blood.

The exact two-byte change passed Windows paired GPU tests: identical particle buffers and impact counts, with the smaller painted areas above. Controlled seeded death-event frames 6 and 120 also matched particle buffers; that diagnostic omitted pair solving and is not a full-game physics equivalence test. A separate ordinary-gameplay smoke test completed 598 frames with pause/resume/restart and no GPU errors or new Windows faults. See `validation/blood-windows-summary.json`.

## Validation of the preceding compatibility build

The following longer and cloud tests apply to SHA `1be63cbf…`, before the two-byte blood-radius adjustment. They are retained as historical evidence, not relabelled as tests of the latest HTML.


- Windows hardware: Chrome 155.0.8059.41, NVIDIA RTX 5070 Ti, driver 591.86, 1280×720, default 2,048 zombies / 32,768 particles. A bounded 60-second test completed 3,600 active frames (10-second gate plus 50 seconds, with an inspection pause), approximately 60 FPS and median reported GPU time 3.87 ms. Movement, 983 rounds, two grenades, wall destruction/fracture, particles and pathfinding ran without game/device errors or new Windows GPU faults. Pause/resume/restart passed and restart restored health, ammunition and world. Simulation continued after the player was downed. Hosted URL testing is a separate deployment check.

- Chromium 140 / Playwright 1.55, SwiftShader WebGPU: 155 frames, default 2,048 zombies and 32,768 particles; movement, firing, voxel destruction, grenade/melee input, pause, restart and demo; no JavaScript or GPU errors. Software-renderer coverage does not establish hardware performance.
- Cloud run: https://github.com/TrentSterling/trentsterling.github.io/actions/runs/38620762717
- `validation/cloud-browser.json` contains the browser report; `assets/tiny-zombies-v9.png` is an actual game capture from that run.
- All 37 compute and 6 render pipelines compiled on the tested Windows NVIDIA configuration without errors or warnings.

## Provenance and reproduction

Source: user-uploaded `tiny_zombies_v9.html` on October 14, 2026.

Original SHA-256: `787cdb9b13b91e27313e550826580e4030ce314fb571299ec171ddf051f99349`

Compatibility repair SHA-256: `1be63cbf1a3887251b0b26067133e71068f7c820c96f5f1c28a9b8718c72f6df`

Current `index.html` SHA-256: `c487bdb1aabeddb7c0ee6edcb2d059aabb2c32ea1be5cfa7a0c34717da3a4fc4`

With Python and Node.js available, reproduce from your preserved original using:

`python tools/make_v9_scratch_candidate.py /path/to/tiny_zombies_v9.html /tmp/reproduced.html`

Then apply `python tools/reduce_floor_stamps.py /tmp/reproduced.html /tmp/current.html` to reproduce the current release.

The scripts verify source and output hashes and checks JavaScript syntax. The crashing original is not the published entry point. No third-party runtime dependencies were found; no new license grant is asserted by this repository.
