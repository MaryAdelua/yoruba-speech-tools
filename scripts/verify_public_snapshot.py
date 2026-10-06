"""Verify published study artifacts without acoustic dependencies."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'evaluation/public_snapshot_manifest.json').read_text(encoding='utf-8'))
failed=[]
for item in manifest['files']:
 p=root/item['path']
 if not p.is_file() or p.stat().st_size!=item['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:failed.append(item['path'])
print(json.dumps({'files_checked':len(manifest['files']),'failures':failed},indent=2))
raise SystemExit(bool(failed))
