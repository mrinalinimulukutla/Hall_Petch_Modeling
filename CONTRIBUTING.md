# Contributing

Workflow for students working on this project.

## Branching model

- `main` is the canonical state. **Do not push directly.** Every change goes
  through a pull request.
- Create a feature branch off `main` for each piece of work:
  ```bash
  git checkout main
  git pull
  git checkout -b feature/short-description
  ```
- Keep branches short-lived (days, not weeks). Open a PR as soon as you have
  something worth reviewing — even draft.

## One-time setup

After cloning, install the pre-commit hooks:

```bash
make install        # installs Python deps incl. pre-commit, nbstripout
make setup-hooks    # registers the hooks with git
```

The hooks (`.pre-commit-config.yaml`) run automatically on every `git commit`:
- **nbstripout** strips outputs from `notebook/*.ipynb` so notebook diffs
  stay reviewable (an executed notebook is ~19 MB; the source is ~110 KB)
- **trailing-whitespace** + **end-of-file-fixer** keep text files tidy
- **check-yaml** validates `.github/workflows/*.yml`
- **check-merge-conflict** catches leftover `<<<<<<<` markers

If a hook modifies your staged file, the commit aborts; re-stage and
re-commit:

```bash
git add -u && git commit -m "..."
```

## Commit hygiene

- One logical change per commit.
- Commit messages: imperative subject line ≤ 70 chars, then optional body
  explaining the *why* (not the *what* — the diff shows that).
- If your change updates a CSV in `results/`, also commit the script that
  generated it. Results without a regenerating script are not reproducible.

## Bibliography validation (when adding citations)

Before adding a new `\cite{...}` to `paper/main.tex`, add a validated
entry to `paper/references.bib`. To check every existing entry against
CrossRef:

```bash
make bib-check
```

This catches incorrect titles, wrong author lists, wrong years, and
missing DOIs. CI also runs this as an advisory job on every push.

Known false positives (do not "fix"):
- **Borg2020 / Schneider2021** truncated author lists are correct
- **Tabor1951** correctly cites the original Clarendon Press edition,
  not the 2000 OUP reprint that CrossRef returns
- **Chen2016XGBoost / Akiba2019Optuna** titles are correctly the full
  subtitled forms; CrossRef truncates

See `tools/bib-check/README.md` for the full false-positive list.

## Writing-style check (when editing the paper)

Before opening a PR that touches `paper/main.tex`, run the AI-slop detector:

```bash
make style-check
```

This catches the most reliable signals (NEG-FIRST framing, ESCALATOR words
like "Importantly,", META-NAR phrases like "underscores the importance",
performative DRAMA, etc.). Some flags are **false positives** that
should be preserved as corpus-authentic voice:

- `Notably,` (12× in the author corpus; flags genuine attention-worthy observations)
- `Although X, Y` (102× concessive-before-claim pattern)
- `we note that`, `i.e.,`, `e.g.,` parenthetical qualifiers
- Statistical "leverage" (regression diagnostic, not business jargon)

The CI runs `style-check` on every push as an advisory job (does not
block merges). See `tools/writing-style/README.md` for the full detector
catalog.

## Pull request checklist

Before requesting review, verify:

1. **The notebook still runs end-to-end.**
   ```bash
   cd notebook && jupyter nbconvert --to notebook --execute Hall_Petch_HEA_Analysis.ipynb --output _test.ipynb && rm _test.ipynb
   ```
2. **The report still generates.**
   ```bash
   python report/generate_report.py
   ```
3. **If you touched a script, the script still runs.** Re-run it and commit
   the updated CSV in `results/`.
4. **If you touched the paper, it still builds.**
   ```bash
   cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
   ```
   Then delete the LaTeX auxiliary files (`*.aux`, `*.bbl`, `*.blg`, `*.log`,
   `*.out`, `*.spl`).
5. **No new top-level files.** Place scripts in `scripts/`, results in
   `results/`, raw data in `data/raw/`, derived data in `data/derived/`.

## Path conventions

Never hardcode absolute paths. Use the shared `_config.py` module:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # or .. for figures/
from _config import REPO_ROOT, DATA_DIR, RESULTS_DIR, PLOTS_DIR

df = pd.read_csv(f'{DATA_DIR}/data_with_descriptors.csv')
df_out.to_csv(f'{RESULTS_DIR}/my_new_result.csv', index=False)
plt.savefig(f'{PLOTS_DIR}/my_new_figure.png')
```

## Adding a new analysis

1. Write the script in `scripts/` using the path conventions above.
2. Run it; commit the resulting CSV(s) in `results/` alongside the script.
3. If the analysis warrants a paragraph in the paper or report, add it to
   `paper/main.tex` and/or `report/generate_report.py` and verify both build.
4. If the analysis warrants a notebook cell, edit `notebook/_generate_notebook.py`
   (not the .ipynb directly) and re-run the generator. The notebook is
   generated; manual edits to the .ipynb will be overwritten.

## Adding a new figure

- Figure-generation scripts go in `scripts/figures/`.
- Publication figures (referenced by `paper/main.tex`) save to
  `{PAPER_FIG_DIR}` (i.e., `paper/figures/`).
- Diagnostic / report figures save to `{PLOTS_DIR}` (i.e., `analysis_plots/`)
  with a numeric prefix (next available; current range is 1–73).

## Code review

- Tag the PI (Raymundo) on PRs that touch `paper/`, `report/`, or change
  result interpretations.
- Reviews focus on correctness, reproducibility, and whether the change is
  in scope. Style nits go in inline comments; merge-blocking comments need
  to clearly state what to change.

## Questions

Open a GitHub issue with the `question` label, or message Raymundo directly.
