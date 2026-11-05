# ZIP Contents and Exclusions

`AgentSec-AI-Final.zip` is a clean source distribution of the verified AgentSec
AI project.

## Included

- FastAPI backend source, schemas, tests, requirements and Dockerfile
- React/TypeScript frontend source, lockfile, Nginx configuration and Dockerfile
- C++ security engine, Windows collector source, headers, tests and sample input
- Python signed event uploader
- Docker Compose and CI configuration
- `.env.example` and `.gitignore`
- README and complete documentation set
- Legacy documentation retained for provenance

## Excluded

- `.git` metadata
- Real `.env` files
- `node_modules`
- Python virtual environments
- `__pycache__`, `.pytest_cache`, `.pyc`
- Reproducible `build` and `dist` output
- C++ executables, object files, PDBs and generated collector samples
- Local SQLite databases and journal/WAL files
- Logs, temporary files and backup files such as `main.py.backup`
- Credentials, API keys, signing keys and access tokens

The working project was not cleaned or reset to create the archive. Packaging
copies only allowed source files into a separate staging directory.

