"""Offline audit of selected WAVs, schema, transcripts and descriptive coverage."""
import collections
import hashlib
import json
from pathlib import Path
import statistics
import sys
import zlib

import jsonschema
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from slr86_import import load_indexes,select_pilot


def main():
    out=ROOT/'work/slr86'
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    rows=lambda p:[json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
    manifest=rows(out/'pilot_manifest.jsonl');natural=rows(out/'natural_reference.jsonl')
    indexes=load_indexes(out/'metadata');selected,_=select_pilot(indexes)
    assert [r['source_item_id'] for r in manifest]==[r['source_item_id'] for r in selected]
    assert len(natural)==len(manifest)==120
    assert len({r['example_id'] for r in natural})==120
    schema=read(ROOT/'evaluation/supervised_example.schema.json')
    validator=jsonschema.Draft202012Validator(schema)
    validator.check_schema(schema)
    by_id={r['source_item_id']:r for r in manifest}
    durations=[];counts=collections.Counter();total_bytes=0
    for row in natural:
        validator.validate(row)
        source=row['natural_source'];m=by_id[source['source_item_id']]
        assert source['speaker_id']==m['speaker_id']
        assert row['transcript']['text']==m['transcript_original']
        assert row['transcript']['tone_marked_text']==m['transcript_nfc']
        assert not row['human_annotations'] and not row['acoustic_measurements']
        assert all(v['status']=='UNSCORED' and v['score'] is None for v in row['assessment_targets'].values())
        path=ROOT/row['audio']['path'];b=path.read_bytes()
        assert hashlib.sha256(b).hexdigest()==row['audio']['sha256']
        assert f'{zlib.crc32(b)&0xffffffff:08x}'==m['zip_crc32']
        assert len(b)==m['uncompressed_bytes']
        info=sf.info(path);audio,sr=sf.read(path,always_2d=True)
        assert info.format=='WAV' and sr==48000 and info.subtype=='PCM_16'
        assert audio.shape==(info.frames,1) and np.isfinite(audio).all()
        assert abs(len(audio)/sr-row['audio']['duration_s'])<1e-10
        durations.append(len(audio)/sr);counts[source['speaker_id']]+=1;total_bytes+=len(b)
    assert len(counts)==12 and set(counts.values())=={10}
    assert {p.stem for p in (out/'audio').glob('*.wav')}==set(by_id)
    unusual=[]
    for row in indexes:
        q=row['text_quality']
        odd={k:v for k,v in q['vowel_counts'].items() if k not in 'aeiouẹọ'}
        if odd or q['conflicting_tone_units']:
            unusual.append({'source_item_id':row['source_item_id'],'selected':row['source_item_id'] in by_id,
                            'transcript_original':row['transcript_original'],'unusual_vowels':odd,
                            'conflicting_tone_units':q['conflicting_tone_units'],'action':'human_review_no_automatic_repair'})
    report={'status':'PASS','records':120,'speakers':dict(counts),'schema_valid':True,
            'full_decode_valid':True,'crc_and_sha256_valid':True,'deterministic_selection_valid':True,
            'all_assessments_unscored':True,'format':'mono 48000 Hz PCM_16 WAV',
            'duration_s':{'total':sum(durations),'min':min(durations),'max':max(durations),'median':statistics.median(durations),'mean':statistics.mean(durations)},
            'audio_bytes':total_bytes,'linguistic_pairing':'source metadata only; not listening verified',
            'unusual_transcript_review_items':unusual,
            'legend_discrepancy':'Legend says 1306; its 682+625 and released-index tag counts sum to 1307.'}
    (out/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='unusual_transcript_review_items'},indent=2))


if __name__=='__main__':main()
