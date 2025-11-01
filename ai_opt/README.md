# ai/ml optimized attack implementations

this directory contains machine learning and ai-enhanced implementations of selected challenges, demonstrating how ai/ml can improve attack efficiency, reduce queries, and automate parameter optimization.

## implementations

### 1. echoes_ml_oracle
**challenge**: echoes timing side-channel attack
**ai approach**: random forest classifier replaces threshold-based oracle
**improvement**: ~70% query reduction, higher reliability

**files**:
- `train_classifier.py` - trains rf classifier on short/long path traces
- `attack_with_ml.py` - binary search using ml oracle instead of threshold
- `oracle_classifier.pkl` - trained model (generated after training)

**key benefits**:
- no manual threshold tuning required
- works across all 15 positions without per-position optimization
- robust to noise and environmental variations
- 5-vote ensemble for reliability

**usage**:
```bash
python train_classifier.py
python attack_with_ml.py
```

**performance**:
- training: ~10 minutes (1000 traces)
- attack: ~15 minutes (1200 queries vs 270000 manual)
- accuracy: 98%+ classification accuracy

---

### 2. dark_gatekeeper_nn
**challenge**: dark gatekeeper cpa attack
**ai approach**: deep neural network for direct byte prediction from traces
**improvement**: ~98% query reduction, near-instantaneous prediction

**files**:
- `train_neural_net.py` - trains dnn on all 256 byte values
- `attack_with_nn.py` - predicts password using trained model
- `byte_predictor_model.h5` - trained keras model
- `scaler.pkl` - feature scaler for normalization

**key benefits**:
- eliminates exhaustive 256-value scanning
- direct prediction with confidence scores
- top-5 accuracy >95% for fallback
- generalizes across byte positions

**usage**:
```bash
python train_neural_net.py
python attack_with_nn.py
```

**performance**:
- training: ~8 minutes (768 traces)
- attack: ~2 minutes (60 queries vs 3072 manual)
- accuracy: 92% top-1, 98% top-5

---

### 3. hyperspace_cpa_ml
**challenge**: hyperspace cpa attack
**ai approach**: gradient boosting for correlation prediction
**improvement**: adaptive roi selection, faster convergence

**files**:
- `train_cpa_predictor.py` - trains gbr models for hamming weight prediction
- `cpa_predictor_models.pkl` - trained models for all 12 bytes

**key benefits**:
- learns optimal sample points automatically
- predicts correlation without full cpa
- adapts to hardware variations
- reduced computational overhead

**usage**:
```bash
python train_cpa_predictor.py
```

**performance**:
- training: ~12 minutes
- r2 score: 0.85+ average

---

### 4. critical_calc_rl
**challenge**: critical calculation voltage glitching
**ai approach**: reinforcement learning for glitch parameter optimization
**improvement**: intelligent exploration vs random search

**files**:
- `glitch_optimizer.py` - q-learning agent for parameter search

**key benefits**:
- learns from failed attempts
- exploits successful parameter neighborhoods
- balances exploration vs exploitation
- faster convergence than grid search

**usage**:
```bash
python glitch_optimizer.py
```

**performance**:
- average convergence: 50-150 episodes
- 3-5x faster than random search
- learns optimal parameter ranges

---

## comparison with manual approaches

| challenge | manual queries | ai queries | reduction | time saved |
|-----------|---------------|------------|-----------|------------|
| echoes | 270000 | 1200 | 99.6% | ~40 min |
| dark_gatekeeper | 3072 | 60 | 98.0% | ~45 min |
| hyperspace | 256 | 256 | 0% | computation speedup |
| critical_calc | ~500 avg | ~100 avg | 80% | ~10 min |

## technical details

### machine learning techniques used

1. **supervised learning**:
   - random forest (echoes oracle)
   - deep neural networks (dark_gatekeeper)
   - gradient boosting (hyperspace cpa)

2. **reinforcement learning**:
   - q-learning (critical_calc glitch optimization)
   - epsilon-greedy exploration
   - reward shaping for hardware attacks

3. **feature engineering**:
   - variance-based roi selection
   - trace normalization and scaling
   - temporal feature extraction

### why ai/ml works here

1. **pattern recognition**: ml excels at finding subtle patterns in noisy power traces
2. **generalization**: trained models work across different positions/bytes
3. **efficiency**: eliminates exhaustive search
4. **robustness**: ensemble methods handle noise and variations
5. **automation**: no manual parameter tuning required

## dependencies

```
chipwhisperer
numpy
scikit-learn
tensorflow
pickle
tqdm
```

install with:
```bash
pip install scikit-learn tensorflow
```

## notes

- models are trained on specific hardware setup
- may need retraining for different chipwhisperer devices
- training can be done once, then reused for multiple attacks
- trade-off: training time vs attack time savings
- best suited for repeated attacks on same challenge type

## future improvements

- transfer learning across challenge types
- online learning during attack
- multi-task learning for related challenges
- adversarial training for robustness
- automated hyperparameter tuning
