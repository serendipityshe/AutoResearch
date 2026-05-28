# Code and Baseline Discovery

## Objective

Find code and baselines that make route candidates testable.

## Repository Checks

For every repository, record:

- Official or third-party.
- License.
- Training entrypoint.
- Evaluation entrypoint.
- Dataset preparation instructions.
- Configuration files.
- Pretrained weights.
- Recent maintenance.
- Dependencies and likely environment risk.

## Baseline Classes

Use task-specific baselines plus generic controls.

For segmentation:

- U-Net, U-Net++, nnU-Net, TransUNet, Swin-UNet, task-specific SOTA.

For classification:

- Cross-entropy CNN/ViT, EfficientNet, DenseNet, ResNet.
- Robust-loss or noisy-label baselines when label inconsistency is part of the route.

For domain generalization:

- Pooled training, leave-one-domain-out, domain adversarial or group robustness controls.

## Required Role

Each baseline must explain what it tests:

- Strong generic baseline.
- Prior domain-specific method.
- Ablation control.
- Clinical rule baseline.
- External benchmark baseline.

## Red Flags

- Repo cannot be linked to the claimed paper.
- No license.
- No training or evaluation command.
- Dataset is private but route assumes reproducibility.
- Reported metrics cannot be reproduced because split files are missing.
