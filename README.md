# SparseTrack Dataset

SparseTrack Dataset is a sparse inertial motion capture dataset designed for real-time human motion reconstruction from sparse IMUs.

The dataset was constructed as part of the SparseTrack framework for learning robust distal-proximal kinematic joint decoupling under sparse sensor observations. The dataset combines:

- natural activities of daily living (ADL) motion data derived from the Virginia Tech Natural Motion Dataset (VT-NMD),
- sparse inertial representations extracted from full-body inertial motion capture recordings,
- and a curated set of high-frequency distal isolation motions recorded specifically to mitigate Kinematic Bleed-Through (KBT) problem.

The dataset is intended for:

- sparse inertial motion capture,
- real-time pose reconstruction,
- physics-informed sequence modeling,
- inertial representation learning,
- and kinematic ambiguity resolution under sparse observations.

---

# Dataset Motivation

Sparse IMU motion capture systems often suffer from a phenomenon known as **Kinematic Bleed-Through (KBT)**, where rapid distal joint motions incorrectly induce spurious proximal joint activations during reconstruction.

This issue becomes especially prominent under sparse sensing constraints, where multiple anatomically valid proximal joint configurations may correspond to similar distal inertial observations.

To explicitly address this challenge, the SparseTrack Dataset incorporates a supplementary motion corpus referred to as **Hard Negative Injection Data**. These recordings contain statistically rare but biomechanically valid distal isolation motions that are typically underrepresented in conventional ADL datasets.

Examples include:

- locked-humerus elbow flexion,
- constrained wrist pronation and supination,
- fixed-thigh seated knee extensions,
- and other high-frequency distal articulation tasks.

These motions were recorded under constrained proximal stability conditions in order to explicitly teach the model to decouple distal oscillations from false proximal activations.

---

# Hybrid Dataset Composition

The SparseTrack Dataset is constructed from two complementary sources.

## 1. Natural Motion Corpus

The primary motion corpus is derived from the Virginia Tech Natural Motion Dataset (VT-NMD), consisting of approximately 40 hours of unscripted activities of daily living (ADLs) captured using a full-body Xsens MVN Link inertial motion capture suit.

The original dataset contains:

- locomotion,
- household activities,
- object interaction,
- physical exercises,
- and unconstrained natural human motion.

From the full-body recordings, a sparse sensor mask was applied to retain only the target sparse sensing locations used by SparseTrack.

---

## 2. Hard Negative Injection Dataset

A supplementary motion corpus was recorded to explicitly capture high-frequency distal isolation dynamics.

These recordings were designed to:

- reduce kinematic ambiguity,
- improve distal-proximal decoupling,
- and increase robustness to sparse observation artifacts.

The hard negative recordings do not aim to maximize demographic diversity or motion coverage. Instead, they intentionally target challenging kinematic corner cases that are statistically rare in natural ADL datasets but critical for stable sparse motion reconstruction.

---

# Sparse Sensor Configuration

SparseTrack operates using sparse inertial observations obtained from the following target body segments:

- left upper arm,
- right upper arm,
- left forearm,
- right forearm,
- left thigh,
- right thigh,
- left shank,
- right shank,
- torso.

These sparse observations are transformed into calibrated local inertial representations for downstream motion reconstruction.

---

# Dataset Structure

```text
SparseTrack-Dataset/
├── raw/
├── processed/
├── scripts/
├── reconstruct_raw.py
└── README.md
```

---

# Raw IMU Streams

The `raw/` directory contains reconstructed Movella-compatible IMU streams organized iteration-wise.

Each iteration contains 9 sensor streams:

```text
raw/Iteration X/
├── left_forearm.csv
├── left_shank.csv
├── left_thigh.csv
├── left_upper_arm.csv
├── right_forearm.csv
├── right_shank.csv
├── right_thigh.csv
├── right_upper_arm.csv
└── torso.csv
```

Each raw CSV contains:

- quaternion orientation,
- free acceleration,
- angular velocity,
- and timestamp metadata.

Example schema:

```text
SampleTimeFine
Quat_W
Quat_X
Quat_Y
Quat_Z
FreeAcc_X
FreeAcc_Y
FreeAcc_Z
Gyr_X
Gyr_Y
Gyr_Z
Status
```

---

# Processed VT-NMD Representation

The `processed/` directory contains calibrated VT-NMD formatted inertial representations used by SparseTrack.

Each iteration contains:

```text
processed/Iteration X/
├── left_arm.csv
├── left_leg.csv
├── right_arm.csv
├── right_leg.csv
└── torso.csv
```

The processed representations contain:

- calibrated segment orientations,
- angular velocities,
- free accelerations,
- and frame-wise inertial features.

---

# Calibration & Frame Transformation

Prior to every recording session, a static T-pose calibration was performed to align the sensor coordinate frames with anatomical body frames.

The preprocessing pipeline applies:

1. Coordinate frame permutation  
2. T-pose boresight calibration  
3. Quaternion normalization  

Upper-body segments use:

```text
q_global = [w, y, -x, z]
```

Lower-body segments use:

```text
q_global = [w, y, -x, -z]
```

The calibrated orientation is computed as:

```text
q_calibrated(t) = q_offset ⊗ q_global(t)
```

where the offset quaternion is obtained from the initial T-pose frame.

---

# Scripts

## MVNX → VT-NMD Extraction

```text
scripts/extract_vtnmd_streams_from_mvnx.py
```

Extracts calibrated VT-NMD representations directly from MVNX motion capture recordings.

---

## Raw → Processed Conversion

```text
scripts/extract_vtnmd_streams_from_movella.py
```

Converts raw Movella-compatible IMU streams into canonical VT-NMD processed representations.

---

# License

This project is licensed under the license provided in the root `LICENSE` file.