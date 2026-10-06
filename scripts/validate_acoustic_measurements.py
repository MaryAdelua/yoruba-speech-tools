"""Reproducible Milestone 2 instrument checks; no linguistic scores."""
import argparse
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import sys

import numpy as np
import parselmouth
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from acoustic_analysis import analyze, sha256

PRAAT = dict(time_step=.01, pitch_floor=65., pitch_ceiling=500.,
             max_number_of_candidates=15, very_accurate=False, silence_threshold=.03,
             voicing_threshold=.45, octave_cost=.01, octave_jump_cost=.35, voiced_unvoiced_cost=.14)


def finite(x):
    return float(x) if np.isfinite(x) else None


def csvout(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def compare(path, floor=65., speech_region=None, frame_length=2048):
    report, frames = analyze(path, fmin=floor, frame_length=frame_length)
    y, sr = sf.read(path)
    pitch = parselmouth.Sound(y, sampling_frequency=sr).to_pitch_ac(**{**PRAAT, "pitch_floor": floor})
    pt = pitch.xs()
    pf = pitch.selected_array["frequency"]
    strength = pitch.selected_array["strength"]
    raw = [{"timestamp_s": float(t), "f0_hz": float(f) if f>0 else None,
            "voiced": bool(f>0), "selected_candidate_strength": float(s)} for t,f,s in zip(pt,pf,strength)]
    rows = []
    for frame in frames:
        t = frame["timestamp_s"]
        j = int(np.argmin(abs(pt-t)))
        matched = abs(pt[j]-t) <= .0050001
        a = frame["f0_hz"]
        b = float(pf[j]) if matched and pf[j]>0 else None
        flags = []
        if a is not None and a <= floor*1.05: flags.append("near_pyin_floor")
        if a is not None and frame["voicing_probability"] < .5: flags.append("pyin_probability_below_0.5")
        if a is not None and speech_region and not speech_region[0] <= t < speech_region[1]: flags.append("outside_provisional_speech")
        if matched and (a is not None) != (b is not None): flags.append("voicing_disagreement")
        st = 12*np.log2(a/b) if a and b else None
        if st is not None and abs(st)>1: flags.append("pitch_difference_over_1_semitone")
        if st is not None and abs(abs(st)-12)<1: flags.append("possible_octave_disagreement")
        rows.append({**frame, "praat_timestamp_s": float(pt[j]) if matched else None,
                     "praat_time_offset_s": float(pt[j]-t) if matched else None,
                     "praat_f0_hz": b, "praat_voiced": bool(b) if matched else None,
                     "praat_strength": float(strength[j]) if matched else None,
                     "absolute_difference_hz": abs(a-b) if a and b else None,
                     "signed_difference_semitones": finite(st) if st is not None else None,
                     "flags": "|".join(flags)})
    baseline = np.median([r["praat_f0_hz"] for r in rows if r["praat_f0_hz"]]) if any(r["praat_f0_hz"] for r in rows) else None
    for r in rows:
        r["praat_relative_semitones"] = float(12*np.log2(r["praat_f0_hz"]/baseline)) if r["praat_f0_hz"] else None
    return report, rows, raw, baseline


def summary(rows, start, end):
    selected = [r for r in rows if start <= r["timestamp_s"] < end]
    both = [r for r in selected if r["absolute_difference_hz"] is not None]
    matched = [r for r in selected if r["praat_voiced"] is not None]
    return dict(start_s=start, end_s=end, frames=len(selected),
                pyin_voiced=sum(r["voiced"] for r in selected),
                praat_voiced=sum(bool(r["praat_voiced"]) for r in selected), both_voiced=len(both),
                matched_frames=len(matched), voicing_disagreements=sum(r["voiced"]!=r["praat_voiced"] for r in matched),
                median_absolute_hz=float(np.median([r["absolute_difference_hz"] for r in both])) if both else None,
                median_absolute_semitones=float(np.median([abs(r["signed_difference_semitones"]) for r in both])) if both else None,
                both_within_half_semitone=sum(abs(r["signed_difference_semitones"])<=.5 for r in both),
                over_one_semitone=sum(abs(r["signed_difference_semitones"])>1 for r in both))


def synthetic(directory):
    sr=24000
    t=np.arange(sr*2)/sr
    cases=[]
    for freq in (80,100,150,220,350,450):
        cases.append((f"constant_{freq}", np.full(len(t),float(freq)), np.full(len(t),.2), []))
    cases.append(("silence", np.zeros(len(t)), np.zeros(len(t)), []))
    cases.append(("amplitude_step", np.full(len(t),150.), np.where(t<1,.2,.02), [1.]))
    cases.append(("f0_step", np.where(t<1,100.,220.), np.full(len(t),.2), [1.]))
    cases.append(("short_burst", np.where((t>=.8)&(t<1.2),150.,0.), np.where((t>=.8)&(t<1.2),.2,0.), [.8,1.2]))
    results=[]
    for name,target,amp,boundaries in cases:
        y=amp*np.sin(2*np.pi*np.cumsum(target)/sr)
        path=directory/(name+".wav")
        sf.write(path,y,sr,subtype="FLOAT")
        _,rows,_,_=compare(path)
        csvout(directory/(name+"_frames.csv"), rows)
        for estimator,key in (("pyin","f0_hz"),("praat","praat_f0_hz")):
            eligible=[r for r in rows if .1<=r["timestamp_s"]<1.9 and all(abs(r["timestamp_s"]-b)>.1 for b in boundaries)]
            voiced=[r for r in eligible if target[min(int(round(r["timestamp_s"]*sr)),len(t)-1)]>0]
            errors=[abs(1200*np.log2(r[key]/target[int(round(r["timestamp_s"]*sr))])) for r in voiced if r[key]]
            silent=[r for r in eligible if target[int(round(r["timestamp_s"]*sr))]==0]
            coverage=len(errors)/len(voiced) if voiced else None
            p95=float(np.percentile(errors,95)) if errors else None
            false=sum(r[key] is not None for r in silent)
            # Predetermined engineering checks, not linguistic metrics.
            passed=(not voiced or (coverage>=.95 and p95 is not None and p95<=50)) and false==0
            transition=[r for r in rows if any(abs(r["timestamp_s"]-b)<=.1 for b in boundaries)]
            results.append(dict(case=name,estimator=estimator,steady_voiced_frames=len(voiced),
                coverage=coverage,p95_error_cents=p95,median_error_cents=float(np.median(errors)) if errors else None,
                steady_silence_frames=len(silent),false_voiced_silence_frames=false,passed=bool(passed),
                boundary_frames=len(transition),boundary_voiced_frames=sum(r[key] is not None for r in transition)))
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio",type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    out=args.output_dir.resolve()
    out.mkdir(parents=True,exist_ok=False)
    os.environ.setdefault("MPLCONFIGDIR",str(out/"plot_cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    source=args.audio.resolve()
    before=sha256(source)
    report,rows,raw,pbase=compare(source, speech_region=(.8,1.9))
    csvout(out/"comparison_frames.csv",rows)
    csvout(out/"praat_native_frames.csv",raw)
    csvout(out/"flagged_frames.csv",[r for r in rows if r["flags"]])
    sensitivity=[]
    for floor in (50.,80.):
        _,other,_,_=compare(source,floor,speech_region=(.8,1.9))
        csvout(out/f"comparison_floor_{int(floor)}.csv",other)
        sensitivity.append({"floor_hz":floor,"full":summary(other,0,8.2),"speech":summary(other,.8,1.9),
                            "original_floor_frames":[r for r in other if any(abs(r["timestamp_s"]-a["timestamp_s"])<1e-8 for a in rows if a["f0_hz"]==65.)]})
    y,sr=sf.read(source)
    t=np.arange(len(y))/sr
    times=np.array([r["timestamp_s"] for r in rows])
    fig,axes=plt.subplots(3,1,figsize=(12,8),sharex=True)
    axes[0].plot(t,y,lw=.4)
    axes[0].set_ylabel("Amplitude (full scale=1)")
    axes[1].plot(times,[r["rms_dbfs"] for r in rows],lw=1)
    axes[1].set_ylabel("Window RMS (dBFS)")
    axes[2].specgram(y,Fs=sr,NFFT=1024,noverlap=768,cmap="magma",vmin=-120,vmax=-55)
    axes[2].set_ylim(0,3000)
    axes[2].set_ylabel("Frequency (Hz)")
    for ax in axes:
        ax.axvspan(.8,1.9,color="green",alpha=.12,label="Provisional speech: 0.8–1.9 s")
        ax.set_xlim(0,len(y)/sr)
    axes[0].legend()
    axes[0].set_title("Full recording: waveform, amplitude and spectrogram — boundaries NOT human-verified")
    axes[2].set_xlabel("Time in assistant.wav (s)")
    fig.tight_layout(); fig.savefig(out/"waveform.png",dpi=150); plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
    for key,label in (("f0_hz","pYIN"),("praat_f0_hz","Praat raw AC")):
        axes[0].plot(times,[r[key] if r[key] else np.nan for r in rows],".-",ms=2,label=label)
    for key,label in (("relative_pitch_semitones","pYIN"),("praat_relative_semitones","Praat raw AC")):
        axes[1].plot(times,[r[key] if r[key] is not None else np.nan for r in rows],".-",ms=2,label=label)
    for ax in axes:
        ax.axvspan(.8,1.9,color="green",alpha=.08)
        ax.legend(); ax.grid(alpha=.2); ax.set_xlim(0,2.2)
    axes[0].set_ylabel("Estimated F0 (Hz)")
    axes[0].set_title("Independent estimators; gaps retained; green = provisional speech")
    axes[1].set_ylabel("Relative pitch (semitones)\nSeparate full-clip estimator medians")
    axes[1].set_xlabel("Time in assistant.wav (s)")
    fig.tight_layout(); fig.savefig(out/"f0_overlay.png",dpi=150); plt.close(fig)
    synth=out/"synthetic"; synth.mkdir()
    results=synthetic(synth)
    csvout(out/"synthetic_results.csv",results)
    regions={name:summary(rows,a,b) for name,a,b in [("pre_speech",0,.8),("provisional_speech",.8,1.9),("after_speech",1.9,8.2)]}
    amplitude={}
    for name,a,b in [("pre_speech",0,.8),("provisional_speech",.8,1.9),("after_speech",1.9,8.2)]:
        segment=y[int(a*sr):int(b*sr)]
        amplitude[name]={"rms_dbfs":finite(20*np.log10(np.sqrt(np.mean(segment**2)))),"peak_amplitude":float(np.max(abs(segment)))}
    result={"source":report["source"],"source_preserved":sha256(source)==before,
        "pyin_method":report["method"],"praat_method":{"algorithm":"raw autocorrelation (not filtered autocorrelation)","praat_version":parselmouth.PRAAT_VERSION,"parselmouth_version":parselmouth.VERSION,"settings":PRAAT,"effective_window_s":3/65},
        "preprocessing":"None; decoded original samples; no trimming, gain, denoising, smoothing or deletion.",
        "pyin_additional_defaults":{"n_thresholds":100,"beta_parameters":[2,18],"boltzmann_parameter":2,"resolution_semitones":.1,"max_transition_rate":35.92,"switch_prob":.01,"no_trough_prob":.01},
        "visualization":{"waveform":"all original samples","spectrogram":{"NFFT":1024,"noverlap":768,"frequency_display_hz":[0,3000],"display_db_limits":[-120,-55]},"smoothing":"none"},
        "alignment":"Nearest Praat center within 5 ms of each pYIN center; no interpolation. Unavailable coverage and unvoiced remain null. Native Praat grid retained.",
        "normalization":{"equation":"12*log2(F0/estimator_full_clip_voiced_median)","pyin_baseline_hz":report["normalization"]["reference_f0_hz"],"praat_baseline_hz":finite(pbase),"caution":"Separate medians can hide systematic offsets; disagreement uses raw frequency ratio instead."},
        "thresholds":{"near_floor_factor":1.05,"low_pyin_probability":.5,"strong_agreement_semitones":.5,"large_disagreement_semitones":1.,"possible_octave_difference_semitones":[11,13],"synthetic_boundary_exclusion_s":.1,"synthetic_min_coverage":.95,"synthetic_max_p95_cents":50},
        "speech_region":{"start_s":.8,"end_s":1.9,"status":"PROVISIONAL_NOT_HUMAN_VERIFIED","note":"Range under investigation; waveform and spectral evidence do not establish linguistic content."},
        "regions":regions,"regional_amplitude":amplitude,"floor_frames":[r for r in rows if r["f0_hz"]==65.],
        "floor_sensitivity":sensitivity,"synthetic_results":results,"scores":report["scores"],
        "limitations":["Estimator agreement is not ground truth.","Praat candidate strength and pYIN probability are different quantities, not calibrated confidence scores.","Synthetic checks exclude +/-100 ms around transitions; boundary frames retained separately.","Signal inspection cannot verify that a sound is meaningful Yoruba speech."]}
    (out/"validation.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"regions":regions,"amplitude":amplitude,"synthetic_checks_passed":sum(r["passed"] for r in results),"synthetic_checks_total":len(results),"floor_frame_times":[r["timestamp_s"] for r in result["floor_frames"]],"source_preserved":result["source_preserved"]},indent=2))


if __name__=="__main__":
    main()
