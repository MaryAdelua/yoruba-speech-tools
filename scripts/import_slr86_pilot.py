"""Prepare SLR86 pilot, then optionally fetch selected ZIP members via HTTP ranges."""
import argparse
import collections
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request
import zipfile
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from slr86_import import BASE,SEED,RangeFile,load_indexes,select_pilot,aggregate,ensure_metadata
from yoruba_orthographic_units import words_and_syllables


def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def csvout(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire',action='store_true')
    args=parser.parse_args()
    out=ROOT/'work/slr86';meta=out/'metadata';meta.mkdir(parents=True,exist_ok=True)
    ensure_metadata(meta)
    items=load_indexes(meta);selected,speakers=select_pilot(items)
    seed={'seed':SEED,'algorithm':'Python random.Random, sorted pools, six speakers/group, ten clips/speaker sampled without replacement',
          'exclusions':['abrupt','external'],'selected_speakers':speakers,'candidate_summary':aggregate(items),
          'note':'No duration-based selection before audio inspection. No tone restoration. Exclusions favor quieter reference material; other tags retained.'}
    dump(out/'selection.json',seed)
    log=[];archives={};mapping={}
    try:
        for gender in ('female','male'):
            url=BASE+f'yo_ng_{gender}.zip';remote=RangeFile(url,log);archive=zipfile.ZipFile(remote)
            infos=archive.infolist()
            archives[gender]=(archive,remote)
            catalog=[{'name':i.filename,'compressed_bytes':i.compress_size,'uncompressed_bytes':i.file_size,'crc32':f'{i.CRC:08x}','compression':i.compress_type} for i in infos]
            dump(meta/f'archive_{gender}.json',{'url':url,'total_archive_bytes':remote.size,'headers':remote.headers,'members':catalog})
            for i in infos:
                if i.filename.lower().endswith('.wav'):
                    item=Path(i.filename).stem
                    if item in mapping:raise ValueError('Duplicate archive audio ID')
                    mapping[item]=(gender,i)
            for i in infos:
                if Path(i.filename).name=='LICENSE':
                    b=archive.read(i)
                    if b!=(meta/'LICENSE').read_bytes():raise ValueError('Archive license differs from official metadata')
                    (meta/f'archive_LICENSE_{gender}').write_bytes(b)
                if Path(i.filename).name=='line_index.tsv':
                    b=archive.read(i);(meta/f'archive_index_{gender}.tsv').write_bytes(b)
                    external=(meta/f'line_index_{gender}.tsv').read_text(encoding='utf-8-sig').splitlines()
                    internal=b.decode('utf-8-sig').splitlines()
                    if sorted(external)!=sorted(internal):raise ValueError('Archive/index transcript mismatch')
        if set(mapping)!=set(r['source_item_id'] for r in items):raise ValueError('Audio inventory does not exactly match transcript IDs')
        manifest=[]
        for r in selected:
            gender,i=mapping[r['source_item_id']]
            manifest.append({**r,'archive_url':BASE+f'yo_ng_{gender}.zip','archive_member':i.filename,
                             'zip_crc32':f'{i.CRC:08x}','compressed_bytes':i.compress_size,'uncompressed_bytes':i.file_size})
        manifest_path=out/'pilot_manifest.jsonl'
        body=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in manifest)
        if manifest_path.exists() and manifest_path.read_text(encoding='utf-8')!=body:raise RuntimeError('Existing pilot differs; refuse replacement')
        manifest_path.write_text(body,encoding='utf-8')
        csvout(out/'pilot_manifest.csv',[{k:r[k] for k in ('source_item_id','speaker_id','released_gender_group','transcript_original','transcript_nfc','archive_url','archive_member','zip_crc32','compressed_bytes','uncompressed_bytes')} for r in manifest])
        dump(out/'transcript_quality.json',{'whole_corpus':aggregate(items),'selected':aggregate(selected),
             'per_selected_item':[{k:r[k] for k in ('source_item_id','text_quality')} for r in selected],
             'limitations':['Underdot presence does not prove lexical correctness. e and ẹ / o and ọ are distinct and retained.',
                 'Missing tone marks cannot be inferred from unmarked vowels alone. Do not label all unmarked vowels M without review.',
                 'NFC normalization is canonical encoding only; original transcripts and metadata bytes retained.',
                 'Bracketed recording annotations retained; excluded from orthographic coverage counts.']})
        shapes=collections.Counter();syllables=set();wordset=set()
        for r in selected:
            clean=re.sub(r'\[[^]]+\]','',r['transcript_nfc'])
            for w in words_and_syllables(clean):
                wordset.add(w['text'].lower())
                for s in w['syllables']:
                    syllables.add(s['orthographic_form'].lower())
        coverage={'orthographic_coverage':aggregate(selected),'speaker_counts':dict(collections.Counter(r['speaker_id'] for r in selected)),
                  'unique_written_words':len(wordset),'unique_heuristic_syllable_forms':len(syllables),
                  'heuristic_syllable_inventory':sorted(syllables),'phonetic_coverage_status':'NOT_VERIFIED: written-form diversity only; no gold phoneme/nucleus alignment',
                  'duration':{'status':'pending_audio_acquisition'}}
        if args.acquire or not (out/'coverage.json').exists():
            dump(out/'coverage.json',coverage)
        acquisition={'status':'prepared_only','full_archives_downloaded':False,'selected_compressed_audio_bytes':sum(r['compressed_bytes'] for r in manifest),
                     'archive_sizes_bytes':{g:remote.size for g,(a,remote) in archives.items()},'method':'Only selected member payloads and ZIP metadata via HTTP Range; never fall back to full archive',
                     'index_inventory_matches':True,'failed':[],'acquired':0}
        if args.acquire:
            import soundfile as sf
            audio_dir=out/'audio';audio_dir.mkdir(exist_ok=True)
            validated=[];natural=[]
            for r in manifest:
                item=r['source_item_id'];gender,i=mapping[item];path=audio_dir/(item+'.wav')
                try:
                    if path.exists():
                        b=path.read_bytes()
                    else:
                        b=archives[gender][0].read(i) # zipfile validates CRC on read
                    if len(b)!=i.file_size or zlib.crc32(b)&0xffffffff!=i.CRC:raise ValueError('ZIP integrity mismatch')
                    if not path.exists():path.write_bytes(b)
                    info=sf.info(path)
                    if info.samplerate!=48000 or info.channels!=1 or info.subtype!='PCM_16' or info.frames<=0:raise ValueError('Unexpected WAV format')
                    sample={'source_item_id':item,'speaker_id':r['speaker_id'],'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(path),
                            'duration_s':info.duration,'frames':info.frames,'sample_rate_hz':info.samplerate,'channels':info.channels,'subtype':info.subtype,'bytes':len(b),
                            'zip_crc32_verified':True,'id_pairing_status':'official_index_and_archive_member_match','linguistic_pairing_status':'NOT_LISTENING_VERIFIED'}
                    validated.append(sample)
                    template=json.loads((ROOT/'evaluation/voice_interactions/supervised_example_001.v0.2.json').read_text(encoding='utf-8'))
                    template.pop('generation');template.update({'example_id':'slr86:'+item,'sample_type':'natural_reference','audio':{k:sample[k] for k in ('path','sha256','duration_s')},
                        'speech_domain':'multi_genre_read_speech','provenance':{'source_url':r['archive_url'],'source_revision':archives[gender][1].etag,'parent_record_ids':[item],
                           'processing_history':[],'capture_notes':'Original released mono 48 kHz PCM WAV; no resampling, denoising, trimming or gain changes.'},
                        'transcript':{'text':r['transcript_original'],'source':f"OpenSLR SLR86 line_index_{gender}.tsv line {r['source_line']}",'status':'source_provided_unreviewed',
                           'tone_marked_text':r['transcript_nfc'],'tone_mark_status':'source_preserved'},
                        'acoustic_measurements':[],'speaker_normalized_measurements':[],'human_annotations':[],'annotation_history':[],
                        'analysis_design':{'mode':'not_assigned','paired_natural_example_ids':[],'reference_cohort_id':'slr86-pilot-860120','text_match_status':'not_checked'},
                        'alignment_artifacts':[],'natural_source':{'dataset':'OpenSLR SLR86','dataset_version':'official-release-snapshot-by-ETag-and-hashes','source_item_id':item,
                           'license':{'identifier':'CC-BY-SA-4.0','source_url':BASE+'LICENSE','status':'verified_for_planned_use','planned_use':'Local acoustic research; no redistribution in this run',
                                      'attribution':'Copyright 2018, 2019, 2020 Google, Inc.; Gutkin et al., Developing an Open-Source Corpus of Yoruba Speech, Interspeech 2020',
                                      'obligations':['Retain attribution and license','Identify modifications','Apply compatible share-alike terms to shared adaptations'],'verified_at':datetime.now(timezone.utc).isoformat()},
                           'speaker_id':r['speaker_id'],'speaker_id_status':'source_provided','speaker_metadata':{'gender':gender,'age_range':None,'dialect':None,'native_speaker_status':'Native Standard Yoruba reported at corpus level; individual not reverified'}}})
                    natural.append(template)
                    print(f'{len(validated)}/120 {item} {info.duration:.3f}s',flush=True)
                except Exception as exc:
                    acquisition['failed'].append({'source_item_id':item,'error':str(exc)})
                    if isinstance(exc,RuntimeError):break
            durations=[r['duration_s'] for r in validated]
            coverage['duration']={'status':'measured_from_WAV_headers','total_s':sum(durations),'min_s':min(durations) if durations else None,'max_s':max(durations) if durations else None,'mean_s':sum(durations)/len(durations) if durations else None}
            coverage['speaker_duration_s']={s:sum(r['duration_s'] for r in validated if r['speaker_id']==s) for s in speakers}
            dump(out/'coverage.json',coverage);dump(out/'audio_validation.json',validated)
            (out/'natural_reference.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in natural),encoding='utf-8')
            acquisition.update({'status':'complete' if len(validated)==120 and not acquisition['failed'] else 'incomplete','acquired':len(validated),
                'audio_bytes':sum(r['bytes'] for r in validated),'audio_duration_s':sum(durations),
                'missing_ids':sorted(set(r['source_item_id'] for r in selected)-set(r['source_item_id'] for r in validated)),
                'ready_for_descriptive_acoustic_extraction':len(validated)==120 and not acquisition['failed'],
                'linguistic_transcript_pairing':'Source metadata matched; human listening verification not performed.'})
        if args.acquire or not (out/'acquisition.json').exists():
            dump(out/'acquisition.json',acquisition)
        print(json.dumps(acquisition,indent=2),flush=True)
    finally:
        dump(meta/'range_requests_latest.json',log)
        dump(meta/('range_requests_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'),log)
        for a,remote in archives.values():a.close();remote.close()


if __name__=='__main__':main()
