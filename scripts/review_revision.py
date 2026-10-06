"""Enforce user-requested human-review revision policy for future ingestion."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'work/slr86'
def require_current(review,kind):
    policy=DATA/'human_review_revision_policy.json'
    if not policy.exists():return
    expected={'natural':'natural_qc_review_v2','paired':'paired_native_listener_review_v2'}[kind]
    if review.get('review_version')!=2 or review.get('review_session_id')!=expected:
        raise ValueError('Superseded or unversioned review rejected. Use the completed '+expected+'.json export; earlier evidence requires an explicit user exception.')
    if kind=='natural':
        if not review.get('reviewer','').strip():raise ValueError('V2 reviewer identifier is required')
        if len(review.get('items',[]))!=20 or any(r.get('review_status')!='reviewed' or r.get('confidence') not in ('low','medium','high') for r in review['items']):raise ValueError('Complete all 20 v2 natural QC judgments and confidence fields before ingestion')
    else:
        path=DATA/'natural-baseline-001/qc-ingest-v2/qc_human_review.original.json'
        if not path.exists():raise ValueError('Ingest the completed natural_qc_review_v2.json first. Both v2 reviews are required before the next human/acoustic analysis.')
        require_current(json.loads(path.read_text(encoding='utf-8-sig')),'natural')
