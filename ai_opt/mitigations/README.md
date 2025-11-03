# AI/ML-Powered Mitigation Strategies

LLM-generated and ML-enhanced countermeasures demonstrating defensive capabilities.

## Approach

1. **LLM-Generated Code Patches**: LLMs analyze vulnerabilities and generate secure implementations
2. **ML-Based Anomaly Detection**: Classifiers detect ongoing attacks in real-time
3. **AI-Optimized Countermeasures**: ML optimizes defense parameters (future work)

## Directory Structure

```
mitigations/
├── llm_patches/                    # LLM-generated secure code (8 challenges)
│   ├── gatekeeper_mitigation.md / gatekeeper_patch.c
│   ├── sorters_song_mitigation.md / sorters_song_patch.c
│   ├── critical_calc_mitigation.md / critical_calc_patch.c
│   ├── hyperspace_mitigation.md / hyperspace_patch.c
│   ├── dark_gatekeeper_mitigation.md / dark_gatekeeper_patch.c
│   ├── echoes_mitigation.md / echoes_patch.c
│   ├── ghost_blood_mitigation.md / ghost_blood_patch.c
│   └── alchemist_mitigation.md / alchemist_patch.c
│
├── anomaly_detector/               # ML attack detection
│   ├── train_detector.py
│   └── monitor_realtime.py
│
├── noise_optimizer/                # Future work
├── mitigation_comparison.py        # Visualization tool
└── README.md
```

## LLM-Generated Patches (8 Challenges)

### Set 1
**Gatekeeper**: Constant-time comparison, random delays, volatile qualifiers
**Sorters Song**: Constant-time swaps, shuffling, XOR blinding, random delays
**Critical Calculation**: Triple Modular Redundancy, canary values, timing bounds

### Set 2
**Hyperspace**: Boolean masking (first/second-order), operation shuffling, random delays
**Dark Gatekeeper**: Boolean masking, operation shuffling, dummy operations

### Set 3
**Echoes**: Constant-time access patterns, array shuffling, XOR blinding
**Alchemist**: Second-order masking (3-share), clock jitter, operation shuffling
**Ghost Blood**: ARX cipher masking (boolean/arithmetic), bit-sliced rotation, dummy operations

## ML Anomaly Detection

**Approach**: Isolation Forest classifier trained on normal vs attack patterns
**Features**: Request timing, query frequency, parameter distributions
**Countermeasures**: Rate limiting, account lockout, logging, adaptive defenses

## Notes

- All 8 challenges achieve 0% attack success after mitigation (atleast within the Chipwhisperer Nano's scope)
- Models trained on specific hardware (may need retraining for different devices)
- LLM patches provide defense-in-depth with multiple countermeasure layers
