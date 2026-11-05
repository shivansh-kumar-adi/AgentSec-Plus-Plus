# Test Report

Date: 2026-11-05. Results below are recorded only from commands actually run.

## Passed

- Original C++ engine compiled with MSVC 19.44.
- Original C++ assertion suite: 6/6 passed.
- Backend integration suite: 1 passed. It covered health, password login, RBAC
  agent registration, HMAC-signed event ingestion, incident creation, and
  deterministic investigation.
- Windows collector compiled with MSVC after implementation.
- Process snapshot produced six newline-delimited events; all six parsed as
  valid JSON.
- Frontend strict TypeScript check and Vite production build passed (2,428
  modules transformed). Vite reported a non-fatal 602.67 kB chunk-size warning.
- Compose configuration interpolation/schema validation passed with temporary
  validation secrets. Docker client 29.6.1 is installed.
- Python backend/uploader sources passed bytecode compilation.
- Replay test verified that a reused nonce is rejected with HTTP 409.

## Failed / corrected during development

- PATH MinGW `g++` cannot start because of an illegal system DLL relocation;
  MSVC is the supported compiler on this host.
- Initial Windows TCP snapshot used an API that returned no size on this host.
  The replacement `GetTcpTable2` implementation compiled, but the runtime call
  returned Windows error 5 (access denied) in this execution sandbox. No TCP
  events were claimed as tested.
- First frontend dependency installation did not finish and the first build
  could not find `tsc`; the resumed install completed. A missing optional native
  Lightning CSS package then failed bundling; after adding the platform package,
  the production build passed.

## Not executed yet

- CMake build (CMake is not installed on this workstation).
- Linux collector (not implemented).
- Authentication event collection (not implemented).
- Backend load, WebSocket, negative replay, and authorization matrix tests.
- Docker Compose build/run. The Docker Desktop Linux daemon was not running
  (`dockerDesktopLinuxEngine` named pipe absent), so only config validation ran.
- Full collector-to-uploader-to-backend end-to-end run.
- Real response execution; by design, only safe simulation is implemented.

