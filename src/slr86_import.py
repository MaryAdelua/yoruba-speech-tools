"""Bounded official SLR86 ZIP-member acquisition and descriptive text inspection."""
import collections
import hashlib
import io
import json
from pathlib import Path
import random
import re
import unicodedata as ud
import urllib.request

BASE='https://openslr.trmal.net/resources/86/'
SEED=860120


def ensure_metadata(directory):
    """Fetch small official metadata only; immutable cached files are reused."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    records=[]
    for name in ('LICENSE','about.html','line_index_female.tsv','line_index_male.tsv','annotation_info.txt'):
        path=directory/name
        headers={}
        if not path.exists():
            with urllib.request.urlopen(BASE+name,timeout=45) as response:
                data=response.read(2_000_001)
                if len(data)>2_000_000:raise RuntimeError('Metadata size limit exceeded')
                headers=dict(response.headers)
            path.write_bytes(data)
        records.append({'name':name,'url':BASE+name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'headers_if_newly_fetched':headers})
    (directory/'metadata_checksums.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    return records


class RangeFile(io.RawIOBase):
    """Never consume a full archive response; only verified bounded HTTP 206 reads."""
    def __init__(self,url,log,budget=64*1024*1024):
        self.url=url;self.log=log;self.pos=0;self.used=0;self.budget=budget
        with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=45) as r:
            self.size=int(r.headers['Content-Length']);self.etag=r.headers.get('ETag')
            self.headers=dict(r.headers)
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        if not 0<=self.pos<=self.size:raise ValueError('Invalid remote seek')
        return self.pos
    def read(self,n=-1):
        n=min(self.size-self.pos,n if n>=0 else self.size-self.pos)
        if n==0:return b''
        if n>8*1024*1024 or self.used+n>self.budget:raise RuntimeError('Bounded transfer limit reached; no full-archive fallback')
        start=self.pos;end=start+n-1
        headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'}
        if self.etag:headers['If-Match']=self.etag
        with urllib.request.urlopen(urllib.request.Request(self.url,headers=headers),timeout=60) as r:
            if r.status!=206:raise RuntimeError('STOP: range not honored. Full archive requires user approval; body not read.')
            if r.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.size}':raise RuntimeError('Unexpected Content-Range')
            data=r.read(n+1)
            if len(data)!=n:raise RuntimeError('Incomplete/oversize range')
        self.pos+=n;self.used+=n
        self.log.append({'url':self.url,'start':start,'end':end,'bytes':n,'etag':self.etag,'sha256':hashlib.sha256(data).hexdigest()})
        return data


def inspect_text(text):
    clean=re.sub(r'\[[^]]+\]','',text)
    clusters=re.findall(r'[^\W\d_][\u0300-\u036f]*|[\s\-’\']',ud.normalize('NFD',clean).lower())
    vowels=[];counts=collections.Counter();nasal_candidates=0;nasal_onsets=0
    for i,g in enumerate(clusters):
        base=g[0]
        if base in 'aeiou':
            label=base+('̣' if '\u0323' in g else '')
            counts[ud.normalize('NFC',label)]+=1
            vowels.append(g)
            if i+1<len(clusters) and clusters[i+1][0]=='n':nasal_candidates+=1
        if base in 'mn' and i+1<len(clusters) and clusters[i+1][0] in 'aeiou':nasal_onsets+=1
    explicit=sum('\u0301' in g or '\u0300' in g or '\u0304' in g for g in vowels)
    return {'nfc_changed':text!=ud.normalize('NFC',text),'nfd_changed':text!=ud.normalize('NFD',text),
            'vowel_units':len(vowels),'explicit_tone_units':explicit,'unmarked_vowel_units':len(vowels)-explicit,
            'conflicting_tone_units':sum('\u0301' in g and '\u0300' in g for g in vowels),
            'replacement_characters':text.count('\ufffd'),
            'vowel_counts':dict(counts),'nasal_vowel_spelling_candidates':nasal_candidates,
            'nasal_consonant_spelling_candidates':nasal_onsets,
            'n_letters':sum(g[0]=='n' for g in clusters),'m_letters':sum(g[0]=='m' for g in clusters),
            'annotations':re.findall(r'\[([^]]+)\]',text)}


def load_indexes(directory):
    items=[];seen=set()
    for gender,prefix in [('female','yof'),('male','yom')]:
        for number,line in enumerate((Path(directory)/f'line_index_{gender}.tsv').read_text(encoding='utf-8-sig').splitlines(),1):
            item,text=line.split('\t',1)
            if not re.fullmatch(prefix+r'_\d{5}_\d{11}',item):raise ValueError(f'Unexpected source ID: {item}')
            if item in seen:raise ValueError('Duplicate source ID')
            seen.add(item)
            items.append({'source_item_id':item,'speaker_id':'_'.join(item.split('_')[:2]),'released_gender_group':gender,
                          'transcript_original':text,'transcript_nfc':ud.normalize('NFC',text),'source_line':number,'text_quality':inspect_text(text)})
    return items


def select_pilot(items,seed=SEED):
    rng=random.Random(seed);selected=[];chosen=[]
    for gender in ('female','male'):
        groups=collections.defaultdict(list)
        for row in items:
            if row['released_gender_group']==gender and not set(row['text_quality']['annotations'])&{'abrupt','external'}:
                groups[row['speaker_id']].append(row)
        eligible=sorted(s for s,rows in groups.items() if len(rows)>=10)
        if len(eligible)<6:raise ValueError('Insufficient eligible speakers')
        for speaker in sorted(rng.sample(eligible,6)):
            chosen.append(speaker)
            selected.extend(rng.sample(sorted(groups[speaker],key=lambda x:x['source_item_id']),10))
    return sorted(selected,key=lambda x:x['source_item_id']),chosen


def aggregate(items):
    total=collections.Counter();vowels=collections.Counter();annotations=collections.Counter()
    for row in items:
        q=row['text_quality']
        for key in ('vowel_units','explicit_tone_units','unmarked_vowel_units','conflicting_tone_units','replacement_characters','nasal_vowel_spelling_candidates','nasal_consonant_spelling_candidates','n_letters','m_letters'):
            total[key]+=q[key]
        vowels.update(q['vowel_counts']);annotations.update(q['annotations'])
    return {'items':len(items),'speakers':len(set(r['speaker_id'] for r in items)),
            'totals':dict(total),'vowel_counts':dict(vowels),'annotation_counts':dict(annotations),
            'non_nfc_items':sum(r['text_quality']['nfc_changed'] for r in items),
            'no_explicit_tone_items':sum(r['text_quality']['explicit_tone_units']==0 for r in items),
            'explicit_tone_mark_rate':total['explicit_tone_units']/total['vowel_units'] if total['vowel_units'] else None,
            'interpretation':'Explicit-mark rate is NOT completeness. Unmarked vowels can represent mid tone or missing annotation; no automatic restoration or correctness inference.',
            'nasal_proxy_limit':'Spelling candidates only; n can mark nasalization or a consonant. Counts do not establish phonetic realization.'}
