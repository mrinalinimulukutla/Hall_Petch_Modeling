# Literature review — ML-audited Hall–Petch strengthening in FCC HEAs

**Purpose:** survey of journal publications and findings relevant to the `paper_v2` manuscript
(best-practices framework for ML prediction of YS and HV in FCC MPEAs), organized by the
manuscript's seven topic areas. Compiled 2026-07 from five parallel web-search sweeps.

**How to read the tags:**
- `[cited]` — already in `paper/references.bib` (69 entries checked)
- `[NEW]` — candidate addition; **validate with `bib-check-cli` against CrossRef before adding** (CLAUDE.md §5)
- `[verify]` — surfaced in search but author list / DOI not fully confirmed; check before citing
- `[foundational]` / `[recent]` — pre-2020 anchor vs 2020–2026 result

---

## 1. Hall–Petch and grain-size scaling laws in FCC HEAs/MPEAs

### Foundational anchors
- Hall (1951); Petch (1953) `[cited]` — the d^-1/2 law.
- Cordero, Knight & Schuh, *Prog. Mater. Sci.* (2016) `[cited]` — pure-metal k_HP compilation; population exponent n ≈ 0.40.
- Otto et al., *Acta Mater.* 61 (2013) `[cited]` — Cantor alloy HP: σ₀ ≈ 125 MPa, k_HP ≈ 494 MPa·µm^1/2.
- Yoshida et al., *Scripta Mater.* 134 (2017) `[cited]` — CoCrNi: high σ₀ ≈ 218 MPa, moderate k_HP ≈ 265.
- Hansen, *Scripta Mater.* 51 (2004), doi:10.1016/j.scriptamat.2004.06.002 `[NEW][foundational]` — canonical short review of boundary strengthening regimes; the standard citation for the physical interpretation of k_HP in FCC metals.
- Liu W.H. et al., *Scripta Mater.* (2013) `[NEW][foundational]` — first Cantor-alloy grain-growth + HP companion to Otto 2013.

### Composition dependence of σ₀ vs k_HP — directly on the manuscript's Tier 3
- **Yoshida, Ikeuchi, Bhattacharjee, Bai & Tsuji, "Effect of elemental combination on friction stress and Hall–Petch relationship in FCC high/medium entropy alloys," *Acta Mater.* 171 (2019) 201–215** `[NEW][foundational]` — HPT + annealing across CoCrFeMnNi subsets; extracted friction stresses fit a lattice-distortion SSS model. *The closest published analog to our σ₀-extraction logic; should be cited in §4.3 and the Introduction.*
- Li J.X. et al., *Mater. Res. Lett.* 12 (2024) 399–407, doi:10.1080/21663831.2024.2337211 `[NEW][recent]` — k_HP = 1100 MPa·µm^1/2 in a Mo-bearing FCC HEA via Mo grain-boundary segregation; chemistry at the boundary can roughly double the slope.
- Banerjee group, *Mater. Res. Lett.* (2021), doi:10.1080/21663831.2020.1871440 `[NEW][recent]` — Al additions to CoFeNi/CoCrFeNi raise k_HP via Ni–Al nano-cluster coherency strains (APT evidence); a concrete chemistry→k_HP mechanism.
- (CoCrMnNi)₁₀₀₋ₓFeₓ study, *Intermetallics* (2021) `[NEW][verify][recent]` — both σ₀ and k_HP fall monotonically with Fe, tracking unstable SFE; clean single-variable composition→k_HP demonstration.
- Non-equiatomic NiCoCrFe study, *Intermetallics* (2025) `[NEW][verify][recent]` — k_HP ordering Co40 (426) > Fe40 (360) > Ni40 (320 MPa·µm^1/2) not explained by segregation or USFE theories alone.
- CoCrFeMnNi vs Cu comparison, *Mater. Sci. Eng. A* (2026) `[NEW][verify][recent]` — k_HP 560 vs 138 MPa·µm^1/2; attributes the gap to lattice friction + low SFE suppressing cross-slip.
- Ke & Sansoz, *Acta Mater.* (2022) 117560 `[NEW][recent]` — segregation-controlled HP limit regimes in nanocrystalline Ag–Cu.

**Relevance:** these works collectively show k_HP *can* vary strongly with chemistry in FCC HEAs — via boundary segregation, nano-clustering, and SFE. Our finding of a composition-independent k_HP (R² = 0.006) within the BIRDSHOT dataset should therefore be framed as dataset-scoped (single-phase, no deliberate segregants, Ni-rich window), not universal. Cite Li 2024 / Banerjee 2021 in the Discussion (§5.3 in main.tex) as the mechanisms our design cannot excite.

### Scaling-law discrimination
- Tian et al., *J. Alloys Compd.* 806 (2019) 992–998 `[NEW][recent]` — temperature-dependent HP in Cantor (77–873 K): both σ₀ and k_HP fall with T; k_HP is not a fixed constant even at fixed composition.
- **Gu, Stiles & El-Awady, "A statistical perspective for predicting the strength of metals: revisiting the Hall–Petch relationship using machine learning," *Acta Mater.* 266 (2024) 119631** `[NEW][recent]` — probabilistic ML over >10⁶ simulated microstructures concludes d^-1/2 remains statistically valid once other microstructural features are marginalized; a counterweight to the Dunstan–Bushby critique. *Directly parallel to our Tier-1 conclusion — high-priority citation.*
- Data-driven modified HP form, *Acta Mater.* (2022) `[NEW][verify][recent]` — data-driven re-derivation of grain-size–strength law; precedent for SR-style discovery of scaling forms.
- **Gap confirmed:** no published information-theoretic (AIC/BIC/Bayesian) scaling-law comparison on HEA datasets was found — our Tier 1 appears to be the first.

### Inverse HP / nanocrystalline breakdown (context only)
- Naik & Walley, *J. Mater. Sci.* (2020), doi:10.1007/s10853-019-04160-w `[NEW][recent]` — modern review of HP and inverse-HP.
- Jones et al., *Sci. Rep.* 10 (2020), doi:10.1038/s41598-020-66701-7 `[NEW][recent]` — first inverse-HP evidence in single-phase CoCrFeMnNi.
- Ji & Wu, *Scripta Mater.* 221 (2022) 114950 `[NEW][recent]` — SRO + GB segregation suppress inverse-HP softening below ~12 nm.

---

## 2. Solid-solution strengthening theories and their validation

### Curtin-group arc (VLC and successors)
- Varvenne, Luque & Curtin (2016); Varvenne & Curtin (2017) `[cited]` — the FCC misfit-volume theory.
- Yin & Curtin, *npj Comput. Mater.* 5 (2019) 14, doi:10.1038/s41524-019-0151-x `[NEW][foundational]` — parameter-free VLC prediction 583 vs measured 527 MPa for RhIrPdPtNiCu; the cleanest demonstration that VLC works when inputs are DFT-quality.
- Yin, Yoshida, Tsuji & Curtin, *Nat. Commun.* 11 (2020) 2507, doi:10.1038/s41467-020-16083-1 `[NEW][recent]` — NiCoCr misfit volumes; VLC captures strength largely without SRO. (*Check overlap with existing `Yin2020` key — that key is the npj FCC/BCC strengthener screening paper; this is a separate work.*)
- Maresca & Curtin, *Acta Mater.* 182 (2020) 144–162 and 235–249, doi:10.1016/j.actamat.2019.10.015 `[NEW][recent]` — BCC screw and edge extensions; context for the protocol's transferability claim to BCC HEAs.
- **Bracq, Laurent-Brocq, Varvenne et al., *Acta Mater.* 177 (2019) 266–279** `[NEW][foundational]` — nanoindentation on 24 single-phase FCC Co-Cr-Fe-Mn-Ni alloys rationalized by VLC with experimental inputs only. *The most direct experimental VLC benchmark; belongs next to our SSS audit (SI §S3, Discussion §5.1).*

### Inputs, critiques, hybrids
- Ikeda, Grabowski & Körmann, *Mater. Charact.* 147 (2019) 464–511 `[NEW][foundational]` — canonical review of SQS/CPA inputs for SSS.
- Liang et al. (LLNL), *npj Comput. Mater.* (2025), doi:10.1038/s41524-025-01910-0 `[NEW][recent]` — computational alchemy: stiffness misfit rivals size misfit. (*Check against existing `Liang2026` key — likely the same work or its companion arXiv:2502.19637; do not double-cite.*)
- Coury, Kaufman & Clarke, *Acta Mater.* 175 (2019) 66–81 `[NEW][foundational]` — athermal/thermal SSS decomposition in refractory HEAs; Labusch-type high-throughput estimates.
- Liu S., Lee & Balachandran, *J. Appl. Phys.* 132 (2022) 105105 `[NEW][recent]` — Bayesian ML supplies elastic-constant inputs to a VLC-type model; legitimizes the hybrid physics+ML strategy.
- Wen et al., *Acta Mater.* 212 (2021) 116917 `[cited as Wen2021SSS]` — **verify venue in references.bib**: search confirms *Acta Materialia*, not npj Comput. Mater.

### Short-range order (complication to random-solution SSS)
- Zhang R. et al., *Nature* 581 (2020) 224–227, doi:10.1038/s41586-020-2275-z `[NEW][recent]` — SRO raises SFE and hardness in CrCoNi.
- Antillon et al., *Acta Mater.* 190 (2020) 29–42 `[NEW][recent]` — MD/MC quantification of CSRO strengthening.
- Rasooli & Daly, *Scripta Mater.* (2025) `[NEW][recent]` — finds no significant SRO–strengthening coupling in CrCoNi; useful counterweight. *Cite the trio together when noting SRO as an un-modeled channel in Limitations.*

---

## 3. ML for HEA strength/hardness prediction

### Composition-based models (validation protocols noted)
- Chang, Jui, Lee & Yeh, *JOM* 71 (2019) 3433, doi:10.1007/s11837-019-03704-4 `[NEW][foundational]` — ANN hardness + simulated annealing; validated by synthesizing designed alloys.
- Bhandari et al., *Mater. Today Commun.* 26 (2021) 101871 `[NEW][recent]` — RF yield strength for refractory HEAs; random split + experimental check.
- Yang C. et al., *Acta Mater.* 222 (2022) 117431 `[NEW][recent]` — SVM hardness with five descriptors selected by a four-step pipeline; **average-deviation-type descriptors beat means** — independent support for our variance-over-means principle.
- Giles et al., *npj Comput. Mater.* 8 (2022) 235, doi:10.1038/s41524-022-00926-0 `[NEW][recent]` — GPR + UQ for RHEA high-T yield strength; repeated k-fold (stated).
- Zhang et al., *Comput. Mater. Sci.* 205 (2022) 111185 `[NEW][recent]` — GA-based descriptor selection for hardness ML.
- Steingrimsson et al., *npj Comput. Mater.* 7 (2021) 152 `[NEW][recent]` — physics-based bilinear log-log σ(T) model; *Appl. Mater. Today* 31 (2023) 101747 follow-up `[NEW][recent]`.

### Microstructure/processing-aware ML (rare — the manuscript's lane)
- Jeon et al., *J. Alloys Compd.* 828 (2020) 154386 `[NEW][recent]` — ANN hardness paired with microstructure exploration (W-bearing HEAs).
- Laser-AM hardness ML, *JOM* 75 (2023), doi:10.1007/s11837-023-06174-x `[NEW][verify][recent]` — processing route as one-hot input.
- DNN optimization study, *Materialia* (2024), S2589152924001595 `[NEW][verify][recent]` — inputs include **grain size, rolling amount, annealing temperature**. *Closest published precedent to our d-channel; read in full before citing.*
- **Gap confirmed:** several 2024–2026 papers explicitly list "no grain size in features" as their limitation; none found using grain-size dispersion (SD_grain) as a predictor. Every composition-based study above uses random splits; none report group/batch CV.

### Campaigns, datasets, reviews
- Rao et al., *Science* 378 (2022) 78–85, doi:10.1126/science.abo4940 `[NEW][recent]` — closed-loop ML discovery of Invar HEAs (17 syntheses); the flagship active-learning citation alongside BIRDSHOT `[cited]`.
- Domain-knowledge-constrained active learning, *Mater. Des.* 223 (2022) 111186 `[NEW][recent]`.
- Gorsse, Nguyen, Senkov & Miracle, *Data in Brief* 21 (2018) 2664 + 2020 corrigendum `[NEW][foundational]` — the other major MPEA property database beside Borg `[cited]`; the corrigendum is itself a citable data-quality artifact.
- Liu X., Zhang & Pei, *Prog. Mater. Sci.* 131 (2023) 101018 `[NEW][recent]` — the comprehensive ML-for-HEA review.
- Berry & Christofidou, *Mater. Sci. Technol.* (2025), doi:10.1177/02670836241272086 `[NEW][recent]` — largest MPEA training set ≈ 1252 points, most studies ≤ 200; ammunition for the sparse-data framing.
- Explainable-ML hardness on Al–Co–Cr–Cu–Fe–Ni (204 samples), *Mater. Today Commun.* (2025) `[NEW][verify][recent]` — nearly our element family, R² 0.90–0.97 under random CV, no group CV: a ready-made example of the validation gap we quantify.

---

## 4. Symbolic regression in materials science

- Ghiringhelli, Ouyang et al., *Phys. Rev. Mater.* 2 (2018) 083802 `[NEW][foundational]` — the core SISSO methods paper (distinct from the cited Ouyang2018).
- Ouyang et al., *J. Phys. Mater.* 2 (2019) 024002 `[NEW]` — multi-task SISSO.
- TorchSISSO, *J. Comput. Sci.* (2024), arXiv:2410.01752 `[NEW][recent]` — the implementation our SISSO runs use (deck credits TorchSISSO); should be cited in Methods.
- Bartel et al., *Nat. Commun.* 9 (2018) 4168 `[NEW][foundational]` — SISSO Gibbs-energy descriptor; the landmark generalizing SR descriptor.
- Perovskite µ/t descriptor, *Nat. Commun.* 11 (2020) 3513 `[NEW][recent]` — SR compressed into a deployable design rule.
- Purcell et al., *npj Comput. Mater.* (2025), doi:10.1038/s41524-025-01596-4 `[NEW][recent]` — SISSO inside a discovery workflow.
- Vickers-hardness SR descriptor, *J. Comput. Sci.* (2024), arXiv:2304.12880 `[NEW][recent]` — closed-form HV from B, G, ν for borides/carbides/nitrides; precedent for our Eq. (HV elbow), different material class.
- SR + domain adaptation for HEA hardness, *J. Mater. Inform.* 4 (2024), doi:10.20517/jmi.2024.71 `[NEW][recent]` — nearest methodological neighbor in the HEA-hardness space.
- Wang, Wagner & Rondinelli, *MRS Commun.* 9 (2019) 793, doi:10.1557/mrc.2019.85 `[NEW][foundational]` — the SR-in-materials primer.
- La Cava et al., NeurIPS D&B (2021) `[NEW][recent]` — SRBench; the accepted cross-engine benchmark, justifying our matched-inputs PySR-vs-SISSO comparison.
- **Muckley, Saal, Meredig et al., *Digital Discovery* 2 (2023) 1425, doi:10.1039/D3DD00082F** `[NEW][recent]` — interpretable models lose little vs black-box in extrapolation (better in ~40% of tasks). *High-priority: the empirical backbone for our "interpretable + audited beats black-box in deployment" argument.*
- Loftis et al., *J. Phys. Chem. A* 125 (2021) 435 `[NEW][recent]` — SR formulae extrapolate better than black-box on thermal conductivity.

---

## 5. Validation and generalization pitfalls in materials ML

- **Meredig et al., *Mol. Syst. Des. Eng.* 3 (2018) 819, doi:10.1039/C8ME00012C** `[NEW][foundational]` — introduces LOCO-CV; random-split CV overestimates discovery performance. *The foundational citation for our LOBO protocol — must be cited in §3.4.*
- Li Q. et al. (MD-HIT), *npj Comput. Mater.* 10 (2024), doi:10.1038/s41524-024-01426-z `[NEW][recent]` — dataset redundancy inflates random-split metrics; directly supports our pseudo-replication argument (23% shared compositions).
- Li K. et al., *Nat. Commun./PMC* (2023) `[NEW][recent]` — redundancy in large materials datasets.
- Li K., DeCost, Choudhary, Greenwood & Hattrick-Simpers, *npj Comput. Mater.* 9 (2023) 55, doi:10.1038/s41524-023-01012-9 `[NEW][recent]` — temporal distribution shift degrades both GNN and descriptor models; OOD diagnostics.
- OOD materials-property benchmark, *npj Comput. Mater.* 10 (2024), doi:10.1038/s41524-024-01316-4 `[NEW][recent]`.
- Applicability-domain determination, arXiv:2406.05143 (2024) `[NEW][recent]` — KDE feature-distance thresholds; conceptual kin of our singularity/deployment envelope.
- Stanev et al., *npj Comput. Mater.* 4 (2018) 28 `[NEW][foundational]` — the superconductor-Tc exemplar that Meredig's critique targets.
- Wang A.Y.-T. et al., *Chem. Mater.* 32 (2020) 4954, doi:10.1021/acs.chemmater.0c01907 `[NEW][recent]` — the standard materials-ML best-practices guide.
- Artrith et al., *Nat. Chem.* 13 (2021) 505, doi:10.1038/s41557-021-00716-z `[NEW][recent]` — chemistry ML checklist.
- Walsh et al. (DOME), *Nat. Methods* 18 (2021) 1122, doi:10.1038/s41592-021-01205-4 `[NEW][recent]` — reporting-checklist template our Table 5 (verdict table) parallels.

---

## 6. Grain-size distribution / heterogeneity effects (the SD_grain channel)

### Classical dispersion theory — predicts *softening* with width
- Kurzydłowski, *Scripta Metall. Mater.* (1990); Kurzydłowski & Bucki, *Acta Metall. Mater.* (1993) `[NEW][foundational]` — volume-weighted HP over the grain-size distribution; broader distribution at fixed mean → lower flow stress (confirmed experimentally in PM aluminum).
- **Berbenni, Favier & Berveiller, *Int. J. Plast.* 23 (2007)** `[NEW][foundational]` — self-consistent model over lognormal distributions: yield stress depends explicitly on the **standard deviation** of the grain-size distribution. *The theoretical anchor for SD_grain as a physical variable.*
- Ramtani et al., *Int. J. Eng. Sci.* (2008); *Mater. Sci. Eng. A* (2009) `[NEW][foundational]` — HP→inverse-HP transition broadens with distribution SD.
- Lavergne, Brenner & Sab, *Comput. Mater. Sci.* (2013) `[NEW][foundational]` — FFT full-field: HP slope and intercept depend on grain-size distribution and stress heterogeneity.
- Lehto et al., *Mater. Sci. Eng. A* 592 (2014) `[NEW][foundational]` — experimental (steel welds): mean-d HP mispredicts when distribution is broad; volume-weighted effective d restores linearity.

### Heterostructure literature — predicts *strengthening* from engineered heterogeneity
- Wang, Chen, Zhou & Ma, *Nature* 419 (2002) 912, doi:10.1038/nature01133 `[NEW][foundational]` — bimodal Cu: distribution shape at fixed mean controls strength–ductility.
- Wu et al., *PNAS* 112 (2015) 14501, doi:10.1073/pnas.1517193112 `[NEW][foundational]` — heterogeneous lamella Ti; HDI strengthening.
- Zhu & Wu, *Mater. Res. Lett.* 7 (2019), doi:10.1080/21663831.2019.1616331 `[NEW][foundational]` — HDI hardening perspective; the standard terminology.
- Yang M. et al., *PNAS* 115 (2018), doi:10.1073/pnas.1807817115 `[NEW][foundational]` — heterogeneous grain structure in a CrCoNi-family MEA: GPa strength + ductility.
- Ameyama et al., *Mater. Res. Lett.* 10 (2022) 440, doi:10.1080/21663831.2022.2057203 `[NEW][recent]` — harmonic-structure review (incl. HEAs).
- Heterostructured HEA review, *Front. Mater.* (2021), doi:10.3389/fmats.2021.792359 `[NEW][recent]`.

### The gap and the sign question
**No prior work uses measured grain-size SD as an explicit regression/ML predictor for YS or HV** — the searches confirm the manuscript's novelty claim. Note the mechanistic tension worth one Discussion sentence: classical dispersion theory (Kurzydłowski/Berbenni) predicts softening as SD grows at fixed mean, while HDI theory predicts strengthening from engineered heterogeneity. Our fitted signs are informative: the PySR YS equation strengthens with SD_grain (HDI-like), while the HV elbow softens with SD_grain at fixed d (Kurzydłowski-like) — the two properties may sit on opposite sides of this competition, which is itself consistent with the paper's property-specific-modeling thesis.

---

## 7. Hardness–yield strength (Tabor) relations in HEAs

- Zhang, Li & Zhang, *Mater. Sci. Eng. A* 529 (2011) 62, doi:10.1016/j.msea.2011.08.061 `[NEW][foundational]` — the modern generalization of Tabor; >1000 citations.
- Brooks et al., *Mater. Sci. Eng. A* 491 (2008) 412 `[NEW][foundational]` — HV ≈ 3σ_UTS holds, HV ≈ 3σ_y fails in nanocrystalline Ni/Co; caution against naive HV→YS conversion.
- Tiryakioğlu et al., *Mater. Sci. Eng. A* (2015) `[NEW][foundational]` — statistical HV–σ_y conversion methodology; indentation work-hardening explains the intercept.
- **Tian et al., "Correlating strength and hardness of HEAs," *Adv. Eng. Mater.* (2021), doi:10.1002/adem.202001514** `[NEW][recent]` — HV ≈ 3σ holds against *ultimate* strength for work-hardenable FCC HEAs, not yield.
- **Fan, Qu & Zhang, *Acta Metall. Sin. (Engl. Lett.)* 34 (2021) 1461, doi:10.1007/s40195-021-01252-y** `[NEW][recent]` — hundreds of HEAs: YS deviates from HV/3 while UTS follows it; proposes HEA-specific conversion relations. *Together with Tian 2021, the direct literature context for C_eff = 5.13 ± 1.36 — both should be cited in §4.7.*
- Čech et al., *Materials* 14 (2021) 7246, doi:10.3390/ma14237246 `[NEW][recent]` — Cantor-alloy constraint factor H/σ_flow ≈ 2.7 (not anomalous); the excess HV/YS comes from work hardening between yield and ε_r ≈ 0.08 — exactly our Tabor-framework reading.
- Nb–Mo–Ta–W combinatorial libraries, *High Entropy Alloys Mater.* (2022), doi:10.1007/s44210-022-00007-3 `[NEW][recent]` — hardness as the default high-throughput screening observable.
- Detor et al., *Data in Brief* (2022), doi:10.1016/j.dib.2022.108582 `[NEW][recent]` — pairs hardness with an independent ductility screen; documented limits of hardness-only screening (context for our rank-scrambling result).
- Schneider/Laplanche open datasets: MnFeNi (*Data in Brief* 2019), CrFeNi (*Data in Brief* 2021), CrCoNi (*Data in Brief* 2019) `[NEW][recent]` — reusable grain-size–strength compilations; candidate additions to the 82-point external set.

---

## Highest-priority additions (shortlist for references.bib)

| # | Reference | Where it strengthens the paper |
|---|-----------|-------------------------------|
| 1 | Meredig et al. 2018 (LOCO-CV) | Methods §3.4 — foundational for LOBO |
| 2 | Yoshida et al. 2019, *Acta Mater.* 171 | Intro + §4.3 — closest analog to σ₀(comp) extraction |
| 3 | Gu, Stiles & El-Awady 2024, *Acta Mater.* 266 | §4.1 — ML defense of d^-1/2 as model selection |
| 4 | Bracq et al. 2019, *Acta Mater.* 177 | SI §S3 + Discussion — direct experimental VLC benchmark |
| 5 | Berbenni et al. 2007, *IJP* 23 | §4.6/Discussion — SD_grain's theoretical anchor |
| 6 | Zhu & Wu 2019 (HDI) + Wang 2002 | §5 — strengthening side of the heterogeneity argument |
| 7 | Fan, Qu & Zhang 2021 + Tian 2021 | §4.7 — HEA-specific HV/YS ≠ 3 consensus |
| 8 | Muckley et al. 2023, *Digital Discovery* | Discussion — interpretable models extrapolate better |
| 9 | Wang A.Y.-T. et al. 2020, *Chem. Mater.* | Intro/Discussion — best-practices positioning |
| 10 | Rao et al. 2022, *Science* | Intro — flagship closed-loop HEA discovery |
| 11 | Ghiringhelli et al. 2018, *PRM* + TorchSISSO 2024 | Methods §3.3 — correct SISSO provenance |
| 12 | Liu X. et al. 2023, *Prog. Mater. Sci.* | Intro — the ML-for-HEA review anchor |
| 13 | MD-HIT 2024, *npj Comput. Mater.* | Limitations — redundancy/pseudo-replication support |
| 14 | Lehto et al. 2014, *MSEA* 592 | §4.6 — experimental precedent for distribution-aware HP |

## Gaps in the literature that the manuscript fills (confirmed by search)

1. No information-theoretic / Bayesian comparison of grain-size scaling laws on HEA data.
2. No use of grain-size standard deviation as an explicit predictor in any strength/hardness model (physics-side parameterizations exist; feature-side use does not).
3. No group/batch (LOBO-style) cross-validation in the HEA strength/hardness ML literature — random splits universally.
4. No published singularity/deployment audit of symbolic-regression alloy-property equations on independent data.
5. No side-by-side YS-and-HV treatment under one validation protocol; the HV-conversion literature (Tian, Fan) stops at pairwise correlation.

## Cross-check notes against references.bib

- `Wen2021SSS` — verify venue: search indicates *Acta Materialia* 212 (2021) 116917, not npj.
- `Yin2020` — the existing key is the FCC/BCC optimal-strengthener screening paper; the NiCoCr misfit-volume *Nat. Commun.* 11:2507 is a **different** Yin & Curtin 2020 work; add separately if cited.
- `Liang2026` — likely the LLNL computational-alchemy work (npj 2025 / arXiv:2502.19637); confirm before adding a duplicate.
- `Cranmer2023PySR` — confirm it points at arXiv:2305.01582 (the PySR software paper).
- Entries tagged `[verify]` have unconfirmed author lists or DOIs — run `bib-check-cli` (in `~/tools/bib-check/`) against CrossRef before adding, per CLAUDE.md §5.

*Method note: compiled from five parallel web-search sweeps (Hall–Petch/scaling; SSS theories; ML-for-HEA; SR + validation pitfalls; heterogeneity + Tabor). Every entry traces to a live search result; none are from model memory alone. Publications marked `[verify]` should be confirmed before citation.*
