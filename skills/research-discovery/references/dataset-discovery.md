# Dataset Discovery

## Objective

Find datasets that make the research route executable. Dataset discovery is not limited to the latest year; older datasets remain valid if they are public, citable, and still used.

## Search Targets

- Dataset papers.
- Challenge pages.
- Official institutional pages.
- Zenodo, Figshare, TCIA, PhysioNet, Hugging Face, Kaggle.
- Official GitHub repositories.
- Recent papers that use the dataset.

## Required Classification

Classify each candidate into one or more roles:

- `primary`: main training or main benchmark.
- `validation`: threshold selection, calibration, hyperparameters.
- `external_test`: domain shift or cross-center testing.
- `supplementary`: extra robustness, segmentation support, descriptor analysis, or qualitative examples.

## Required Checks

For each dataset, record:

- Task compatibility.
- Sample count and unit: patient, case, image, clip, volume.
- Label type and reference standard.
- Mask, bounding box, descriptor, diagnosis, pathology, or report availability.
- License and access status.
- Split availability and patient-level identifiers.
- Download or mirror risk.
- Whether recent papers still use it.

## Red Flags

- Different mirrors report different sample counts.
- Labels are only inferred from filenames.
- No license or no source-of-truth page.
- No patient identifiers for leakage-safe splitting.
- Dataset is gated but treated as open.
- Dataset supports segmentation but is used as classification without label verification.
