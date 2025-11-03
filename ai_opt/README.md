# AI/ML Optimized Attack Implementations

Machine learning and AI-enhanced implementations demonstrating improved attack efficiency through automated parameter optimization and pattern recognition.

## Implementations

### 1. echoes_ml_oracle
**Challenge**: Echoes timing side-channel
**Approach**: Random Forest classifier replaces threshold-based oracle
**Benefits**: No manual threshold tuning, works across all positions, robust to noise

### 2. dark_gatekeeper_nn
**Challenge**: Dark Gatekeeper DPA
**Approach**: Deep neural network for direct byte prediction
**Benefits**: Eliminates exhaustive scanning, direct prediction with confidence scores

### 3. hyperspace_cpa_ml
**Challenge**: Hyperspace CPA
**Approach**: Gradient boosting for correlation prediction
**Benefits**: Learns optimal sample points automatically, adapts to hardware variations

### 4. critical_calc_rl
**Challenge**: Critical Calculation glitching
**Approach**: Q-learning for parameter optimization
**Benefits**: Learns from failures, exploits successful parameter neighborhoods

## ML Techniques

- **Supervised Learning**: Random Forest, DNNs, Gradient Boosting
- **Reinforcement Learning**: Q-learning with epsilon-greedy exploration
- **Feature Engineering**: Variance-based ROI, trace normalization

## Dependencies

```bash
pip install scikit-learn tensorflow chipwhisperer numpy tqdm
```

## Notes

- Models trained on specific hardware (may need retraining for different devices)
- Training done once, reused for multiple attacks
- Best suited for repeated attacks on same challenge type
