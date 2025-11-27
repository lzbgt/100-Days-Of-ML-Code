# Barometer Dataset Findings (Nov 20, 2025 runs)

## Context

- Logs: `data/0m.txt`, `0.5m.txt`, `1m.txt`, `1.5m.txt`, `2m.txt` (the anchor dataset is replaced by 0m.txt).
- Tags: BD41E, BD41F; both moved together through nominal 0 → 2 m steps.
- Parser: `extract_baro.py` → `data/baro_readings.csv` (2,914 samples after anchor removal).
- Analysis: `analyze_baro.py` (baseline = first sample per tag; pairing window 0.3 s).

## Key Observations

- Cross-tag consistency (paired samples, 0.3 s window, first-sample baseline):
  - 0m: median +0.000 m, range ≈ ±0.084 m.
  - 0.5m: median +0.000 m, range ≈ ±0.084 m.
  - 1m: median +0.083 m, range –0.000 to +0.167 m (upper tail is during ascent; stationary points stay within ±0.08–0.10 m).
  - 1.5m: median –0.000 m, range –0.084 to +0.167 m (ascent tail).
  - 2m: median +0.083 m, range –0.084 to +0.167 m (ascent tail).
- Takeaway: in level segments the inter-tag delta is generally within ±8–10 cm; ascent ramps can momentarily show up to ~17 cm due to time skew.
- The hypsometric equation itself is behaving correctly; the observed ~1.6 m span for the "2 m" step comes from the measured pressure change (~19 Pa), which physically corresponds to ~1.6 m. A linear k/b fit is still recommended to match your marked heights.
- Zero/scale calibration (this session):
  - Self-baseline medians (per tag):
    - BD41E: 0m −0.335, 0.5m −0.168, 1.0m +0.335, 1.5m +0.752, 2.0m +1.254 (span 1.589 m).
    - BD41F: 0m −0.335, 0.5m −0.168, 1.0m +0.251, 1.5m +0.752, 2.0m +1.254 (span 1.589 m).
  - Use: `h_cal = 1.26 * (h_raw + 0.335)` (1.26 ≈ 2.0 / 1.589) so 0 m → 0, 2 m → 2.0.
  - Equivalent linear form: `h_true ≈ 0.422 + 1.259 * h_raw`.
- Scale shortfall: median heights land ~1.6 m at the “2 m” file → scale ≈ about 0.8× (BD41E scale 0.518, BD41F 0.507 m/m). A ~1.20–1.25× multiplier (or equivalent floor_height tweak) is needed; recompute k/b per session with known steps for best accuracy.
- Auto fit (this session, to targets 0/0.5/1/1.5/2): self k=1.195, b=0.561, RMSE≈0.10 m; anchor k=1.195, b=-0.541, RMSE≈0.10 m. Use these or refit each session when heights change.
- Anchor-as-baseline check (anchor BD41F @ 0m, moving BD41E):
    - Medians: 0m 0.586, 0.5m 0.755, 1.0m 1.256, 1.5m 1.673, 2.0m 2.176 m; spans ~0.17–0.25 m.
    - Errors vs nominal: +0.586, +0.255, +0.256, +0.173, +0.176 m → all < ±0.5 m except the first (offset/bias).
    - Subtracting the first-file bias (~0.586 m) makes all steps fit within ±0.26 m; scale still ~1.26× from hypsometric derived pressures.
- Session dependence: using a baseline from another session (e.g., the removed anchor) introduces a fixed offset (~1.3 m previously). Per-session baselining avoids this.

## Can We Reach ±50 cm?

Yes, with the following:

1) Per-session baseline: zero each tag to its first static segment in the same run (what `--baseline first` does).
2) Scale correction: apply a global height scale of ~1.25× (or set detector `floor_height` accordingly). For this session specifically, `h_cal = 1.26 * (h_raw + 0.335)` maps 0→2 m correctly. Real-time k/b fitting needs known height points; if you only have 0 m on site, set the offset from 0 m and use a precomputed scale (from offline calibration or assumed floor height). Refit when you have new trusted height references.
3) Light smoothing: a short EWMA or the existing rolling reference window (20–30 s, band 0.2 m) keeps random noise in the ±0.1–0.2 m band. Combined with the scale fix, total error stays within ±0.5 m.

## Recommended System Setup

- Zero capture: require a brief stationary period at a known reference (e.g., entrance floor) and store averaged p/T as the session baseline (p0, T0); prompt re-zero if pressure drift >0.3 hPa (~2.5 m).
- Re-zero policy: also re-zero after long gaps or temperature jumps; store the session’s p0/T0 and fitted k/b so logs can be reprocessed consistently.
- Placement: start each run with both tags stationary at the reference height (0 m mark) for a few seconds to lock the baseline.
- Environment: minimize drafts/HVAC transients during baseline; log temperature to keep the hypsometric conversion stable.
- Sampling: keep current ~2 Hz; higher rates add little benefit relative to noise.

## Algorithm Settings (for `analyze_baro.py` / downstream detectors)

- Baseline: `--baseline first` (per tag, per session).
- Scale: multiply derived heights by ~1.26 from this session (or ~1.25 as a round number), or set detector `floor_height` to 2.5 m. Re-fit k/b per session using your measured 0 m and top step.
- Rolling reference (optional): window 20–30 s, band 0.2 m, min duration 20 s to re-zero slow drift.
- Pairing tolerance (cross checks): keep ≤0.3 s.

## Validation Checklist

- After extraction, run: `/mnt/e/venv-wsl/bin/python analyze_baro.py --baseline first`
  - Confirm in `median_by_file.png` that 2 m file lands near 2 m after scale tweak.
  - Check `cross_diff_by_file.png` stays near 0 m.
  - Apply the linear calibration `h_cal = 1.26 * (h_raw + 0.335)` if using this session’s numbers.
- If a constant offset appears across all files, re-baseline in-session; if a uniform scale error appears, adjust the multiplier.

## Remaining Gaps

- Absolute accuracy still depends on ambient pressure stability between baseline and motion; simultaneous fixed-height reference during each run would tighten confidence.
- No data yet above 2 m; extrapolation assumes linearity holds— gather a 0–4 m repeat to verify.
