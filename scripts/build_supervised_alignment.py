"""One-recording review scaffold; reference spelling never certifies realization."""
import argparse
import csv
import html
import json
import os
from pathlib import Path
import sys
import unicodedata

import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from acoustic_analysis import sha256
from tone_parser import tone_sequence


def build(reference, frames):
    text=unicodedata.normalize("NFC",reference["reference_text"])
    # A reviewed orthographic scaffold, not a general nasal syllabification rule.
    reconstructed=[]
    for word in text.split():
        units=[u["syllable"] for u in reference["reference_units"] if u["word"]==word]
        if "".join(units)!=word.replace("-", ""):
            raise ValueError("Reference units do not reconstruct their word")
        reconstructed.append(word)
    records=[]; associations=[]
    last=0
    for index,u in enumerate(reference["reference_units"],1):
        if not last <= u["start_s"] < u["end_s"]:
            raise ValueError("Invalid boundary order")
        last=u["end_s"]
        tones=tone_sequence(u["syllable"])
        if len(tones)!=1: raise ValueError("Pilot requires one written vowel tone unit per reference interval")
        selected=[r for r in frames if u["start_s"]<=float(r["timestamp_s"])<u["end_s"]]
        row={"unit_id":index,"word":u["word"],"reference_syllable":u["syllable"],
             "expected_reference_tone":tones,"tone_source":"orthographic marks in user-supplied reference; no surface-tone inference",
             "start_s":u["start_s"],"end_s":u["end_s"],"duration_s":round(u["end_s"]-u["start_s"],4),
             "boundary_status":reference["boundary_status"],"boundary_basis":u["basis"],
             "flags":"BOUNDARY_UNVERIFIED|NOT_VERIFIED_NUCLEUS_INTERVAL|LOW_PYIN_PROBABILITY"+("|"+u["special_flag"] if u.get("special_flag") else "")}
        for name,key,relative in (("pyin","f0_hz","relative_pitch_semitones"),("praat","praat_f0_hz","praat_relative_semitones")):
            values=[float(r[key]) for r in selected if r[key]]
            rel=[float(r[relative]) for r in selected if r[relative]]
            row[name+"_voiced_frames"]=len(values)
            for label,value in (("median_hz",np.median(values) if values else None),("min_hz",min(values) if values else None),("max_hz",max(values) if values else None),("median_relative_semitones",np.median(rel) if rel else None)):
                row[name+"_"+label]=float(value) if value is not None else None
        row["paired_within_half_semitone_frames"]=sum(r["signed_difference_semitones"]!="" and abs(float(r["signed_difference_semitones"]))<=.5 for r in selected)
        for r in selected:
            crosses=float(r["window_start_s"])<u["start_s"] or float(r["window_end_s"])>u["end_s"]
            associations.append({"unit_id":index,"reference_syllable":u["syllable"],"pyin_window_crosses_proposed_boundary":crosses,**r})
        records.append(row)
    return records,associations


def writecsv(path,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    os.environ.setdefault("MPLCONFIGDIR",str(out/"plot_cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    audio=ROOT/"work/voice_eval/incoming/assistant.wav"
    measurements=ROOT/"work/voice_eval/measurement-validation-002"
    config=ROOT/"evaluation/voice_interactions/supervised_alignment_001.json"
    reference=json.loads(config.read_text(encoding="utf-8"))
    validation=json.loads((measurements/"validation.json").read_text(encoding="utf-8"))
    original=sha256(audio)
    if original!=validation["source"]["sha256"]: raise ValueError("Audio differs from validated measurements")
    with (measurements/"comparison_frames.csv").open(encoding="utf-8",newline="") as f: frames=list(csv.DictReader(f))
    records,associations=build(reference,frames)
    writecsv(out/"syllables.csv",records);writecsv(out/"associated_frames.csv",associations)
    # Preserve earlier recognizer evidence with its original time coordinate system.
    anchor_source=ROOT.parent.parent/"work/yoruba_test_001_local_asr.json"
    anchor=json.loads(anchor_source.read_text(encoding="utf-8"))[-1]
    (out/"anchor_evidence.json").write_text(json.dumps({"source_path":str(anchor_source),"sha256":sha256(anchor_source),"original_record":anchor,"conversion":"assistant_time = original_time - 12.6","status":"unverified CTC token events; not phonetic ground truth"},ensure_ascii=False,indent=2),encoding="utf-8")
    data={"reference":reference,"alignment_status":"SUPERVISED_REVIEW_DRAFT_NOT_CONFIRMED",
          "source_audio":{"path":str(audio),"sha256":original,"unchanged":sha256(audio)==original},
          "measurement_source":{"path":str(measurements/"comparison_frames.csv"),"sha256":sha256(measurements/"comparison_frames.csv")},
          "normalization":validation["normalization"],"dimensions":{"lexical_tone_accuracy":"reference H/M/L labels only; observed correctness unassessed","segmental_pronunciation":"nasal/consonant/vowel realization and duration unassessed; human perception preserved, not acoustically proven","prosody_intonation":"utterance contour preserved; correctness unassessed","fluency_rhythm":"unassessed; do not infer from general naturalness observation","semantic_content_correctness":"intended content recognizable to listener; independent correctness assessment not performed here"},
          "syllables":records,"scores":validation["scores"],
          "limitations":["Syllables are reference hypotheses, not proof of separate realized syllables.","Final rùn/ún division at 1.78 s is a review placeholder; no independent acoustic boundary established.","Statistics include all available estimator outputs in each center-time interval; not a set of certified reliable frames.","Estimator agreement is descriptive, not proof of accuracy. Frame-level flags remain intact.","Frames span proposed boundaries: pYIN window 85.33 ms; Praat effective window about 46.15 ms.","No measurements of nasal duration, phoneme identity, or lexical-tone correctness are inferred."]}
    (out/"alignment.json").write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    y,sr=sf.read(audio);times=np.arange(len(y))/sr
    fig,axes=plt.subplots(4,1,figsize=(14,11),sharex=True)
    axes[0].plot(times,y,lw=.5);axes[0].set_ylabel("Original amplitude")
    axes[1].specgram(y,Fs=sr,NFFT=512,noverlap=448,cmap="magma",vmin=-120,vmax=-55)
    axes[1].set_ylim(0,4000);axes[1].set_ylabel("Spectrogram (Hz)")
    ft=[float(r["timestamp_s"]) for r in frames]
    for key,label in (("f0_hz","pYIN"),("praat_f0_hz","Praat")):
        axes[2].plot(ft,[float(r[key]) if r[key] else np.nan for r in frames],".-",ms=2,label=label)
    for key,label in (("relative_pitch_semitones","pYIN"),("praat_relative_semitones","Praat")):
        axes[3].plot(ft,[float(r[key]) if r[key] else np.nan for r in frames],".-",ms=2,label=label)
    axes[2].set_ylabel("Estimated F0 (Hz)");axes[2].legend()
    axes[3].set_ylabel("Relative semitones");axes[3].set_xlabel("Time in unchanged assistant.wav (s)")
    for i,r in enumerate(records):
        for ax in axes:
            ax.axvspan(r["start_s"],r["end_s"],color="gray" if i%2 else "blue",alpha=.05)
            ax.axvline(r["start_s"],color="black",ls=":",alpha=.6)
        axes[0].text((r["start_s"]+r["end_s"])/2,1.02,r["reference_syllable"]+"\n"+r["expected_reference_tone"],ha="center",va="bottom",transform=axes[0].get_xaxis_transform())
    for ax in axes:
        ax.axvline(1.78,color="red",ls="--",alpha=.6);ax.set_xlim(.70,2.0)
    fig.suptitle("Proposed reference alignment — ALL boundaries require review\nH/M/L = user-reference spelling, not measured tone correctness; red = unresolved final division",y=.995)
    fig.tight_layout(rect=[0,0,1,.92]);fig.savefig(out/"alignment.png",dpi=160);plt.close(fig)
    rel_audio=os.path.relpath(audio,out).replace("\\","/")
    rowshtml="".join(f'<tr><td>{html.escape(r["word"])}</td><td>{html.escape(r["reference_syllable"])}</td><td>{r["expected_reference_tone"]}</td><td>{r["start_s"]:.2f}–{r["end_s"]:.2f}</td><td><button onclick="playInterval({max(0,r["start_s"]-.08)},{r["end_s"]+.08})">Listen with 80 ms context</button></td><td>{html.escape(r["boundary_basis"])}</td></tr>' for r in records)
    page='''<!doctype html><meta charset="utf-8"><title>Supervised Yoruba alignment review</title><style>body{font:17px system-ui;max-width:1400px;margin:30px auto;padding:20px}img{width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #ccc}button{padding:8px}blockquote{background:#f5f3e8;padding:15px}</style><h1>Reference alignment — awaiting native review</h1><p>Reference only: <strong>'''+html.escape(reference["reference_text"])+'''</strong>. Labels do not certify acoustic realization. No tone or pronunciation scores.</p><blockquote>'''+html.escape(reference["human_annotation"])+'''</blockquote><p>All boundaries are provisional. The final rùn/ún split is a review placeholder, not a detected boundary. Listen to the whole utterance first; segment playback can create artificial boundaries.</p><audio id="audio" controls src="'''+html.escape(rel_audio)+'''"></audio><button onclick="playInterval(.7,2.05)">Play utterance with context</button><img src="alignment.png" alt="Provisional syllable alignment"><table><tr><th>Word</th><th>Reference unit</th><th>Reference tone</th><th>Seconds</th><th>Playback</th><th>Boundary evidence</th></tr>'''+rowshtml+'''</table><p>Playback seeks within the original WAV at normal speed and volume; no derived clips or transformations. Give corrections by unit and timestamp. Nasal material has not been removed or duration-normalized.</p><script>const a=document.getElementById('audio');let stop=null;function playInterval(s,e){a.pause();a.currentTime=s;stop=e;a.play()}a.addEventListener('timeupdate',()=>{if(stop!==null&&a.currentTime>=stop){a.pause();stop=null}});a.addEventListener('ended',()=>stop=null);</script>'''
    (out/"review.html").write_text(page,encoding="utf-8")
    if sha256(audio)!=original: raise RuntimeError("Audio changed")
    print(json.dumps(records,ensure_ascii=False,indent=2))


if __name__=="__main__": main()
