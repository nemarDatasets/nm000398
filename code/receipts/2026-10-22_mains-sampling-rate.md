# Receipt: README: mains peaks confirm the release sampling rates

**Claim**: read at the release README rates (A 256 Hz, B-D 512 Hz), all 23 files show a 60 Hz mains peak and none at 30 Hz; B-D also 180 Hz and 212 Hz (300 Hz aliased), A also 120 Hz in 6 of its 7 files.

**PR**: nemarDatasets/nm000398#4, receipt on top of head `477dbefe`.

## Source
- NEMAR nm000398 `origin/main` `b5003d876a657b5fe9c7fc672a4e9897acbb544d`: all 23 `sub-*/ieeg/*_ieeg.{vhdr,eeg}`; each equals that commit (`.eeg` sha256 = git-annex key, `.vhdr` = git blob; column "vhdr+eeg == main"). The rate in each `.vhdr` is the one under test.
- Rates: release README `README_for_SubA_Sleep1.pdf` (Dryad doi:10.5061/dryad.4f92n, version 1), page 1: "Subject A; Sampling Frequency = 256 Hz", "Subject B; Sampling Frequency = 512 Hz", likewise C and D 512 Hz. The copy read is `sourcedata/dryad-4f92n-deidentified/README_for_SubA_Sleep1.pdf`, sha256 `ab560f3b…41bb13` = its git-annex key; `DEIDENTIFICATION_MANIFEST.tsv` lists the Dryad original (sha256 `6404bd77…4fca24`, same length; only the PDF CreationDate/ModDate day differs).
- Article (Pahwa et al. 2015, PLoS ONE, doi:10.1371/journal.pone.0142947), Methods: "sampled at 256 Hz" for all patients.

## Method
- Reader: MNE 1.13.2 `read_raw_brainvision`, `get_data(units="uV")` (stored float32 values, resolution 1), at the header rate.
- Channels with >= 1% of samples at |value| >= 5482 (the +5482.29 / -5482.46 clipping plateaus) are left out ("ch used").
- Spectrum: scipy 1.18.1 `welch`, 4 s Hann segments, 50% overlap (0.25 Hz bins); median over the used channels; dB.
- Peak at f: dB above a straight line fitted (dB vs Hz) to the bins 1-5 Hz on both sides of f; z = that excess / robust SD (1.4826 x MAD) of the flank residuals. A peak (`*`) is z >= 5.
- Targets: 30, 60, 120 Hz at both rates; 44 and 76 Hz (300 and 180 Hz aliased) at 256 Hz; 180 and 212 Hz (300 Hz aliased) at 512 Hz. "top peak Hz": the bin between 6 Hz and Nyquist - 6 Hz with the largest excess; "top at 256 Hz": where that peak would sit if the file were read at the article's 256 Hz.

## Result
Read at 256 Hz (subject A):

| file | vhdr+eeg == main | Hz | h | ch used | 30 Hz | 44 Hz | 60 Hz | 76 Hz | 120 Hz | top peak Hz | top at 256 Hz |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sub-A_task-sleep_acq-part1_run-2 | True | 256 | 0.88 | 64/64 | -0.1 dB, z -1 | -0.1 dB, z -1 | +4.2 dB, z +32* | +0.0 dB, z +0 | +2.2 dB, z +9* | 60 | 60 |
| sub-A_task-sleep_acq-part2_run-2 | True | 256 | 0.88 | 64/64 | -0.4 dB, z -2 | +0.0 dB, z +0 | +1.9 dB, z +7* | +0.3 dB, z +1 | +0.5 dB, z +1 | 60 | 60 |
| sub-A_task-sleep_run-1 | True | 256 | 0.46 | 64/64 | -0.3 dB, z -4 | +5.6 dB, z +44* | +32.6 dB, z +51* | +13.0 dB, z +50* | +26.8 dB, z +16* | 60 | 60 |
| sub-A_task-wake_acq-part1_run-1 | True | 256 | 1.02 | 64/64 | -0.1 dB, z -1 | +1.7 dB, z +22* | +30.7 dB, z +16* | +9.5 dB, z +50* | +26.4 dB, z +12* | 60 | 60 |
| sub-A_task-wake_acq-part1_run-2 | True | 256 | 0.79 | 64/64 | -0.2 dB, z -1 | -0.1 dB, z -1 | +9.0 dB, z +135* | +0.1 dB, z +1 | +6.3 dB, z +98* | 60 | 60 |
| sub-A_task-wake_acq-part2_run-1 | True | 256 | 1.02 | 64/64 | -0.1 dB, z -1 | +1.0 dB, z +14* | +24.8 dB, z +25* | +5.8 dB, z +55* | +25.3 dB, z +21* | 120 | 120 |
| sub-A_task-wake_acq-part2_run-2 | True | 256 | 0.79 | 64/64 | -0.0 dB, z -0 | -0.1 dB, z -1 | +7.5 dB, z +109* | +0.1 dB, z +1 | +4.7 dB, z +41* | 60 | 60 |

Read at 512 Hz (subjects B-D):

| file | vhdr+eeg == main | Hz | h | ch used | 30 Hz | 60 Hz | 120 Hz | top peak Hz | top at 256 Hz | 180 Hz | 212 Hz |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sub-B_task-sleep_acq-part1_run-2 | True | 512 | 0.45 | 63/64 | -0.2 dB, z -1 | +48.2 dB, z +427* | +15.7 dB, z +101* | 60 | 30 | +42.1 dB, z +252* | +36.8 dB, z +181* |
| sub-B_task-sleep_acq-part2_run-2 | True | 512 | 0.45 | 63/64 | -0.1 dB, z -1 | +47.6 dB, z +746* | +15.0 dB, z +188* | 60 | 30 | +42.0 dB, z +282* | +37.2 dB, z +416* |
| sub-B_task-sleep_run-1 | True | 512 | 0.58 | 63/64 | -0.0 dB, z -0 | +46.0 dB, z +465* | +11.8 dB, z +133* | 60 | 30 | +35.7 dB, z +561* | +33.1 dB, z +576* |
| sub-B_task-wake_acq-part1_run-2 | True | 512 | 0.45 | 63/64 | -0.4 dB, z -2 | +44.8 dB, z +657* | +10.8 dB, z +93* | 60 | 30 | +34.1 dB, z +259* | +31.5 dB, z +161* |
| sub-B_task-wake_acq-part2_run-2 | True | 512 | 0.45 | 63/64 | -0.1 dB, z -1 | +45.8 dB, z +590* | +13.3 dB, z +143* | 60 | 30 | +37.9 dB, z +169* | +34.5 dB, z +255* |
| sub-B_task-wake_run-1 | True | 512 | 0.50 | 63/64 | +0.0 dB, z +0 | +47.3 dB, z +386* | +12.7 dB, z +126* | 60 | 30 | +36.9 dB, z +188* | +30.9 dB, z +208* |
| sub-C_task-sleep_acq-part1_run-2 | True | 512 | 0.41 | 64/64 | -0.3 dB, z -3 | +46.0 dB, z +437* | +18.2 dB, z +229* | 60 | 30 | +38.9 dB, z +389* | +35.1 dB, z +260* |
| sub-C_task-sleep_acq-part2_run-2 | True | 512 | 0.41 | 64/64 | +0.1 dB, z +2 | +45.6 dB, z +463* | +17.9 dB, z +197* | 60 | 30 | +38.9 dB, z +493* | +35.3 dB, z +317* |
| sub-C_task-sleep_run-1 | True | 512 | 0.48 | 64/64 | -0.1 dB, z -1 | +45.2 dB, z +735* | +17.1 dB, z +208* | 60 | 30 | +41.1 dB, z +379* | +29.2 dB, z +174* |
| sub-C_task-wake_run-1 | True | 512 | 0.62 | 64/64 | -0.1 dB, z -1 | +43.1 dB, z +657* | +13.9 dB, z +198* | 60 | 30 | +35.8 dB, z +425* | +25.7 dB, z +301* |
| sub-C_task-wake_run-2 | True | 512 | 0.68 | 64/64 | -0.1 dB, z -1 | +45.5 dB, z +570* | +15.6 dB, z +210* | 60 | 30 | +34.2 dB, z +237* | +30.3 dB, z +245* |
| sub-D_task-sleep_acq-part1_run-1 | True | 512 | 0.36 | 64/64 | +0.0 dB, z +0 | +45.9 dB, z +969* | +9.5 dB, z +152* | 60 | 30 | +33.8 dB, z +311* | +34.7 dB, z +51* |
| sub-D_task-sleep_acq-part2_run-1 | True | 512 | 0.36 | 64/64 | +0.1 dB, z +1 | +46.1 dB, z +352* | +9.5 dB, z +150* | 60 | 30 | +33.7 dB, z +288* | +34.6 dB, z +62* |
| sub-D_task-sleep_run-2 | True | 512 | 0.48 | 63/64 | -0.1 dB, z -1 | +43.2 dB, z +422* | +5.5 dB, z +40* | 60 | 30 | +22.9 dB, z +87* | +20.4 dB, z +220* |
| sub-D_task-wake_run-1 | True | 512 | 0.49 | 64/64 | -0.2 dB, z -1 | +46.9 dB, z +569* | +9.9 dB, z +80* | 60 | 30 | +31.7 dB, z +294* | +32.0 dB, z +126* |
| sub-D_task-wake_run-2 | True | 512 | 0.59 | 63/64 | -0.3 dB, z -2 | +43.7 dB, z +725* | +7.3 dB, z +54* | 60 | 30 | +24.1 dB, z +135* | +23.7 dB, z +211* |

- 60 Hz peak in 23 of 23 files (weakest: sub-A_task-sleep_acq-part2_run-2, +1.9 dB, z +7).
- B-D: 180 Hz and 212 Hz peaks in 16 of 16 files.
- A: 120 Hz peak in 6 of 7 files; not in sub-A_task-sleep_acq-part2_run-2 (+0.5 dB, z +1).
- 30 Hz: no peak in any file (z <= +2).
- At the article's 256 Hz, the B-D 60 Hz peak would sit at 30 Hz (16 of 16).

## Coverage
23 of 23 files (13.62 h), all channels except those at the clipping plateaus in >= 1% of samples (63 or 64 of 64 per file).

## Reproduce
```
uv run --no-project --with mne==1.13.2 --with scipy --with pandas python code/receipts/2026-10-22_mains-sampling-rate.py <nm000398 root> <nm000398 git clone>
```
Run on 2026-10-23 (Slurm job 13542298; first run 2026-10-22, job 13449206, at `86629adf`, same tables); the root was a NEMAR copy of `origin/main`, the clone gives `origin/main` for the checks.
