"""c-pahwa (Dryad doi:10.5061/dryad.4f92n; Pahwa et al. 2015 PLoS One) -> iEEG-BIDS (raw).

Source: 23 .mat files, each holding one matrix 'data' (64 channels x samples; v7.3 stored channels x samples, v5 samples x 64),
float64 values that are exactly representable in float32 (checked per file: float32 round trip identical).
No sampling rate, channel names or units in the files. SAMPLING RATE IS TAKEN FROM THE README (README_for_SubA_Sleep1.pdf:
"Subject A; Sampling Frequency = 256 Hz", B/C/D "= 512 Hz"). The article says 256 Hz for all; README per-subject values used.
Files: Sub<X>_<Sleep|Wake><n>[_part<k>].mat -> sub-<X>_task-<sleep|wake>_[acq-part<k>_]run-<n>_ieeg (parts kept as separate files).
Signals written as BrainVision IEEE_FLOAT_32 (values identical); unit µV assumed (not stated in the release).
Usage: python b3w3_convert_pahwa.py <sourcedata_dl> <bids_root>
"""
import hashlib, json, os, re, shutil, sys
import numpy as np, h5py, scipy.io as sio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b3w3_common import wtsv, wjson, write_vhdr, scrub_mat_header, sha256_file

SRC, OUT = sys.argv[1], sys.argv[2]
FS = {"A": 256.0, "B": 512.0, "C": 512.0, "D": 512.0}  # README_for_SubA_Sleep1.pdf
CLIP = 5482.29
report = {"runs": [], "sourcedata": [], "continuity": []}
SD = os.path.join(OUT, "sourcedata", "dryad-4f92n-deidentified"); os.makedirs(SD, exist_ok=True)
last = {}
scans = {}
for n in sorted(x for x in os.listdir(SRC) if x.endswith(".mat")):
    m = re.match(r"Sub([A-D])_(Sleep|Wake)_?(\d)(?:_part(\d))?\.mat$", n)
    s, state, ep, part = m.group(1), m.group(2).lower(), int(m.group(3)), m.group(4)
    p = os.path.join(SRC, n)
    if open(p, "rb").read(10) == b"MATLAB 7.3":
        with h5py.File(p, "r") as hf:
            a = hf["data"][()].T
        fmt = "v7.3"
    else:
        a = sio.loadmat(p)["data"]; fmt = "v5"
    assert a.shape[1] == 64, a.shape
    a32 = a.astype(np.float32)
    lossless = bool(np.array_equal(a32.astype(np.float64), a))
    assert lossless, n
    fs = FS[s]
    S = f"sub-{s}"; D = os.path.join(OUT, S, "ieeg"); os.makedirs(D, exist_ok=True)
    stem = f"{S}_task-{state}" + (f"_acq-part{part}" if part else "") + f"_run-{ep}"
    np.ascontiguousarray(a32).astype("<f4").tofile(os.path.join(D, stem + "_ieeg.eeg"))
    names = [f"ch{i + 1:02d}" for i in range(64)]
    write_vhdr(os.path.join(D, stem + "_ieeg"), 64, fs, names, ["µV"] * 64, comment=f"b3w3_convert_pahwa.py: {n} 'data' matrix as float32 (values identical); sampling rate from README_for_SubA_Sleep1.pdf")
    clip = (np.abs(a) >= CLIP).mean(axis=0)
    rows = [[names[i], "ECOG", "µV", "n/a", "n/a", fs, "grid", "good", "n/a",
             f"column {i + 1} of the release 'data' matrix" + (f"; {100 * clip[i]:.1f}% of samples at the amplitude limit (|x| >= {CLIP})" if clip[i] > 0 else "")] for i in range(64)]
    wtsv(os.path.join(D, stem + "_channels.tsv"), ["name", "type", "units", "low_cutoff", "high_cutoff", "sampling_frequency", "group", "status", "status_description", "description"], rows)
    wjson(os.path.join(D, stem + "_ieeg.json"), {
        "TaskName": state,
        "TaskDescription": ("Wakeful state: epoch in which the patient, free-behaving in the epilepsy monitoring unit, had eyes open and was cognitively active (talking, eating, listening, etc.), identified from video and audio; state unchanged for at least 20 min (article)."
                            if state == "wake" else
                            "Sleep-like state: epoch in which the patient, free-behaving in the epilepsy monitoring unit, appeared asleep on video and audio; state unchanged for at least 20 min (article)."),
        "Instructions": "none: no task; natural behaviour during clinical monitoring",
        "SamplingFrequency": fs,
        "PowerLineFrequency": 60,
        "SoftwareFilters": "n/a",
        "HardwareFilters": {"HighpassFilter": {"CutoffFrequency": 0.1, "Description": "hardware high-pass built into the recording amplifiers (README_for_SubA_Sleep1.pdf)"}},
        "iEEGReference": "n/a (not stated in the release or article)",
        "Manufacturer": "Natus (Nicolet)", "ManufacturersModelName": "Nicolet c128 (amplifiers named in the article)",
        "RecordingDuration": a.shape[0] / fs, "RecordingType": "continuous",
        "ECOGChannelCount": 64, "SEEGChannelCount": 0,
        "iEEGPlacementScheme": "8x8 subdural grid over left frontal, temporal and parietal cortex (article, Fig 2); positions shown only as an image in README_for_SubA_Sleep1.pdf",
        "iEEGElectrodeInfo": "PMT Corporation grids, flat circular platinum electrodes, 2.3 mm exposed diameter (article)",
        "ElectricalStimulation": False,
        "SamplingFrequencySource": "README_for_SubA_Sleep1.pdf (the .mat files store no sampling rate); the article's Methods state 256 Hz",
    })
    scans.setdefault(S, []).append([f"ieeg/{stem}_ieeg.vhdr", "n/a"])
    key = (s, state, ep)
    if part == "2" and key in last:
        prev = last[key]
        d_join = np.abs(a[0] - prev).mean()
        d_typ = np.abs(np.diff(a[:2000], axis=0)).mean()
        report["continuity"].append(dict(recording=f"{s}_{state}{ep}", mean_abs_step_at_join=float(d_join), mean_abs_step_typical=float(d_typ)))
    if part == "1":
        last[key] = a[-1].copy()
    report["runs"].append(dict(file=n, mat_format=fmt, stem=stem, n_samples=int(a.shape[0]), sfreq=fs, float32_lossless=lossless,
                               sha256_float32=hashlib.sha256(a32.astype("<f4").tobytes()).hexdigest(), clipped_fraction_max=float(clip.max())))
    # roundtrip
    import mne
    rr = mne.io.read_raw_brainvision(os.path.join(D, stem + "_ieeg.vhdr"), preload=False, verbose="error")
    k = min(a.shape[0], int(10 * fs))
    ok = rr.n_times == a.shape[0] and np.allclose(rr.get_data(start=0, stop=k) * 1e6, a[:k].T, rtol=1e-6, atol=1e-6) and \
         np.allclose(rr.get_data(start=a.shape[0] - k) * 1e6, a[-k:].T, rtol=1e-6, atol=1e-6)
    report["runs"][-1]["roundtrip_ok"] = bool(ok)
    print(stem, a.shape, fs, "roundtrip", ok, "clipmax", round(float(clip.max()), 3), flush=True)
    del a, a32
for S, rows in scans.items():
    wtsv(os.path.join(OUT, S, f"{S}_scans.tsv"), ["filename", "acq_time"], sorted(rows))
# sourcedata: originals; MAT text-header 'Created on' and PDF creation/modification dates reduced to month+year (same length)
for f in sorted(os.listdir(SRC)):
    if f == "SHA256SUMS":
        continue
    b = open(os.path.join(SRC, f), "rb").read()
    note = "unchanged"
    if f.endswith(".mat"):
        b, ch = scrub_mat_header(b); note = "MAT text header date -> Mmm 01 yyyy" if ch else note
    elif f.endswith(".pdf"):
        nb = re.sub(rb"(D:\d{6})\d\d", rb"\g<1>01", b)
        if nb != b:
            b, note = nb, "PDF metadata CreationDate/ModDate day -> 01 (same length)"
    open(os.path.join(SD, f), "wb").write(b)
    report["sourcedata"].append([f, os.path.getsize(os.path.join(SRC, f)), sha256_file(os.path.join(SRC, f)), hashlib.sha256(b).hexdigest(), note])
wtsv(os.path.join(SD, "DEIDENTIFICATION_MANIFEST.tsv"), ["path", "bytes_original", "sha256_original", "sha256_here", "change"], report["sourcedata"])
os.makedirs(os.path.join(OUT, "code"), exist_ok=True)
for f in (__file__, os.path.join(os.path.dirname(os.path.abspath(__file__)), "b3w3_common.py")):
    shutil.copy(f, os.path.join(OUT, "code", os.path.basename(f)))
json.dump(report, open(os.path.join(OUT, "code", "conversion_report.json"), "w"), indent=1)
print(json.dumps({"runs": len(report["runs"]), "roundtrip_all_ok": all(r["roundtrip_ok"] for r in report["runs"]), "continuity": report["continuity"]}, indent=1))
print("CONVERT_DONE")
