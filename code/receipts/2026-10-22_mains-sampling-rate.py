"""Mains peaks in nm000398 read at the release README sampling rates (A 256 Hz, B-D 512 Hz).

Usage: python 2026-10-22_mains-sampling-rate.py <nm000398 root> <nm000398 git clone>

<nm000398 root> holds the BIDS files read, <nm000398 git clone> gives origin/main (git-annex
keys, text files).
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import scipy
import scipy.signal

REF = "origin/main"
SATURATION = 5482  # |value| of the clipping plateaus (+5482.29 / -5482.46)
MAX_SATURATED = 0.01
SEGMENT_S = 4
FLANK_HZ = (1, 5)
PEAK_Z = 5
ARTICLE_HZ = 256
# mains harmonics and their aliases at each rate
TARGETS = {256: (30, 44, 60, 76, 120), 512: (30, 60, 120, 180, 212)}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


def git(clone: Path, *args: str) -> bytes:
    out = subprocess.run(["git", "-C", clone, *args], capture_output=True)
    assert out.returncode == 0, out.stderr.decode()
    return out.stdout


def same_as_main(root: Path, clone: Path, rel: Path) -> bool:
    """File equals origin/main: sha256 = git-annex key, or bytes = git blob."""
    blob = git(clone, "show", f"{REF}:{rel}")
    if blob.startswith(b"/annex/objects/SHA256E-"):
        return blob.decode().split("--")[1].split(".")[0] == digest(root / rel)
    return blob == (root / rel).read_bytes()


def prominence(log_psd: np.ndarray, f: np.ndarray, i: int) -> tuple[float, float]:
    """dB above a line fitted to the 1-5 Hz flanks, and that excess / robust SD of the flanks."""
    lo, hi = (k * SEGMENT_S for k in FLANK_HZ)
    flanks = np.r_[i - hi : i - lo + 1, i + lo : i + hi + 1]
    fit = np.polyfit(f[flanks], log_psd[flanks], 1)
    residual = log_psd[flanks] - np.polyval(fit, f[flanks])
    excess = log_psd[i] - np.polyval(fit, f[i])
    spread = 1.4826 * np.median(np.abs(residual - np.median(residual)))
    return excess, excess / spread


def main(root: Path, clone: Path) -> None:
    print(f"mne {mne.__version__}, numpy {np.__version__}, scipy {scipy.__version__}")
    print(f"{REF} of the clone: {git(clone, 'rev-parse', REF).decode().strip()}")
    rows = []
    for vhdr in sorted(root.glob("sub-*/ieeg/*_ieeg.vhdr")):
        rel = vhdr.relative_to(root)
        raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
        fs = raw.info["sfreq"]
        x = raw.get_data(units="uV")
        used = np.mean(np.abs(x) >= SATURATION, axis=1) < MAX_SATURATED
        f, psd = scipy.signal.welch(x[used], fs, nperseg=int(SEGMENT_S * fs))
        log_psd = 10 * np.log10(np.median(psd, axis=0))
        row = {
            "file": rel.name.removesuffix("_ieeg.vhdr"),
            "vhdr+eeg == main": all(
                same_as_main(root, clone, rel.with_suffix(s)) for s in (".vhdr", ".eeg")
            ),
            "Hz": f"{fs:g}",
            "h": raw.n_times / fs / 3600,
            "ch used": f"{used.sum()}/{used.size}",
        }
        for hz in TARGETS[int(fs)]:
            db, z = prominence(log_psd, f, int(round(hz * SEGMENT_S)))
            row[f"{hz} Hz"] = f"{db:+.1f} dB, z {z:+.0f}{'*' if z >= PEAK_Z else ''}"
        search = np.flatnonzero((f >= 6) & (f <= fs / 2 - 6))
        top = max(search, key=lambda i: prominence(log_psd, f, i)[0])
        row["top peak Hz"] = f"{f[top]:g}"
        row[f"top at {ARTICLE_HZ} Hz"] = f"{f[top] * ARTICLE_HZ / fs:g}"
        rows.append(row)
    table = pd.DataFrame(rows)
    for fs, group in table.groupby("Hz", sort=False):
        group = group.dropna(axis=1)
        print(f"\n### read at {fs} Hz\n")
        print("| " + " | ".join(group.columns) + " |")
        print("|---" * group.shape[1] + "|")
        for r in group.itertuples(index=False):
            cells = (f"{v:.2f}" if isinstance(v, float) else str(v) for v in r)
            print("| " + " | ".join(cells) + " |")
    print(f"\n{len(table)} files, {table['h'].sum():.2f} h")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
