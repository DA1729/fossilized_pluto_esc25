import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

challenges = ['echoes', 'dark_gatekeeper', 'hyperspace', 'critical_calc']
manual_queries = [270000, 3072, 256, 500]
ai_queries = [1200, 60, 256, 100]
manual_time = [60, 50, 15, 20]
ai_time = [20, 5, 15, 10]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('ai/ml optimization impact analysis', fontsize=16, y=0.995)

ax1 = axes[0, 0]
x = np.arange(len(challenges))
width = 0.35
bars1 = ax1.bar(x - width/2, manual_queries, width, label='manual', color='#e74c3c', alpha=0.8)
bars2 = ax1.bar(x + width/2, ai_queries, width, label='ai/ml', color='#27ae60', alpha=0.8)
ax1.set_ylabel('number of queries', fontsize=11)
ax1.set_title('query count comparison', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(challenges, rotation=15, ha='right')
ax1.legend()
ax1.set_yscale('log')
ax1.grid(axis='y', alpha=0.3)
for i, (m, a) in enumerate(zip(manual_queries, ai_queries)):
    reduction = (1 - a/m) * 100
    ax1.text(i, max(m, a) * 1.5, f'-{reduction:.1f}%', ha='center', fontsize=9, fontweight='bold')

ax2 = axes[0, 1]
bars1 = ax2.bar(x - width/2, manual_time, width, label='manual', color='#e74c3c', alpha=0.8)
bars2 = ax2.bar(x + width/2, ai_time, width, label='ai/ml', color='#27ae60', alpha=0.8)
ax2.set_ylabel('time (minutes)', fontsize=11)
ax2.set_title('execution time comparison', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(challenges, rotation=15, ha='right')
ax2.legend()
ax2.grid(axis='y', alpha=0.3)
for i, (m, a) in enumerate(zip(manual_time, ai_time)):
    time_saved = m - a
    ax2.text(i, max(m, a) + 2, f'-{time_saved}min', ha='center', fontsize=9, fontweight='bold')

ax3 = axes[1, 0]
reduction_pct = [(1 - ai_queries[i]/manual_queries[i]) * 100 for i in range(len(challenges))]
colors = ['#27ae60' if r > 50 else '#f39c12' if r > 20 else '#95a5a6' for r in reduction_pct]
bars = ax3.barh(challenges, reduction_pct, color=colors, alpha=0.8)
ax3.set_xlabel('query reduction (%)', fontsize=11)
ax3.set_title('efficiency improvement', fontsize=12, fontweight='bold')
ax3.grid(axis='x', alpha=0.3)
for i, (bar, val) in enumerate(zip(bars, reduction_pct)):
    ax3.text(val + 2, i, f'{val:.1f}%', va='center', fontsize=10, fontweight='bold')

ax4 = axes[1, 1]
metrics = ['accuracy\n(avg)', 'robustness\n(variance)', 'automation\n(score)', 'speed\n(relative)']
manual_scores = [75, 60, 40, 50]
ai_scores = [92, 85, 95, 80]
x_metrics = np.arange(len(metrics))
bars1 = ax4.bar(x_metrics - width/2, manual_scores, width, label='manual', color='#e74c3c', alpha=0.8)
bars2 = ax4.bar(x_metrics + width/2, ai_scores, width, label='ai/ml', color='#27ae60', alpha=0.8)
ax4.set_ylabel('score (0-100)', fontsize=11)
ax4.set_title('qualitative performance metrics', fontsize=12, fontweight='bold')
ax4.set_xticks(x_metrics)
ax4.set_xticklabels(metrics, fontsize=9)
ax4.legend()
ax4.set_ylim(0, 110)
ax4.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('ai_ml_comparison.png', dpi=300, bbox_inches='tight')
print("saved: ai_ml_comparison.png")

df = pd.DataFrame({
    'challenge': challenges,
    'manual_queries': manual_queries,
    'ai_queries': ai_queries,
    'reduction_%': reduction_pct,
    'manual_time_min': manual_time,
    'ai_time_min': ai_time,
    'time_saved_min': [manual_time[i] - ai_time[i] for i in range(len(challenges))]
})

print("\nperformance comparison summary:")
print(df.to_string(index=False))

df.to_csv('ai_ml_comparison.csv', index=False)
print("\nsaved: ai_ml_comparison.csv")

total_manual_queries = sum(manual_queries)
total_ai_queries = sum(ai_queries)
total_reduction = (1 - total_ai_queries/total_manual_queries) * 100
total_manual_time = sum(manual_time)
total_ai_time = sum(ai_time)
total_time_saved = total_manual_time - total_ai_time

print(f"\noverall statistics:")
print(f"total query reduction: {total_reduction:.1f}%")
print(f"total time saved: {total_time_saved} minutes")
print(f"average improvement: {np.mean(reduction_pct):.1f}% query reduction")
