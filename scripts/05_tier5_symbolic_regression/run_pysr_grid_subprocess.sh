#!/usr/bin/env bash
# Run the 18 PySR grid cells (2 targets × 3 feature sets × 3 operator sets)
# as separate subprocesses to avoid PySR's multi-fit-in-one-process hang.
#
# Usage:  bash scripts/run_pysr_grid_subprocess.sh
# Output: results/pysr_grid/<target>__<fs>__<op>__cell.json (18 files)
#         results/pysr_grid_summary_{YS,HV}.csv (aggregated)
#         results/pysr_grid_full_{YS,HV}.json (aggregated)
set -e
cd "$(dirname "$0")/.."
export PATH="$HOME/.juliaup/bin:$PATH"
PY=/usr/local/anaconda3/bin/python
LOG=/tmp/pysr_grid_subprocess.log
: > "$LOG"

FEATURES=(F1_grain F2_full F3_wen)
OPERATORS=(O1_add_sub O2_add_sub_mul_div O3_full)
TARGETS=(YS HV)

for tgt in "${TARGETS[@]}"; do
    for fs in "${FEATURES[@]}"; do
        for op in "${OPERATORS[@]}"; do
            tag="${tgt}__${fs}__${op}"
            echo "[$(date +%H:%M:%S)] Starting $tag" | tee -a "$LOG"
            PYSR_TARGET=$tgt PYSR_FS=$fs PYSR_OP=$op \
                "$PY" -u scripts/pysr_grid_analysis.py >> "$LOG" 2>&1
            echo "[$(date +%H:%M:%S)] Finished $tag" | tee -a "$LOG"
        done
    done
done

echo "[$(date +%H:%M:%S)] Aggregating ..." | tee -a "$LOG"
PYSR_TARGET=YS PYSR_AGGREGATE_ONLY=1 "$PY" -u scripts/pysr_grid_analysis.py >> "$LOG" 2>&1
PYSR_TARGET=HV PYSR_AGGREGATE_ONLY=1 "$PY" -u scripts/pysr_grid_analysis.py >> "$LOG" 2>&1
echo "[$(date +%H:%M:%S)] Done." | tee -a "$LOG"
