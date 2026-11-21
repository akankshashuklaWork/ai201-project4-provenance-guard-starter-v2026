"""
Score every calibration text through both signals and print one table.

    python calibration_run.py

This calls the signal functions directly (no web service needed), so it is the
quickest way to see which signal is off when a score surprises you.
Columns: model = signal one, style = signal two, mix = combined score.
"""

import detector
import scoring
import stylometry
from calibration_texts import GROUPS


def main():
    print(f"{'group':14} {'#':>2}  {'model':>6} {'style':>6} {'mix':>6}  guess")
    print("-" * 52)

    averages = {}
    for group, texts in GROUPS.items():
        mixes = []
        for i, text in enumerate(texts, 1):
            model = detector.model_signal(text)
            style = stylometry.style_signal(text)
            mix = scoring.combine_signals(model, style)
            guess, _ = scoring.score_to_label(mix)
            mixes.append(mix)
            print(f"{group:14} {i:>2}  {model:6.3f} {style:6.3f} {mix:6.3f}  {guess}")
        averages[group] = sum(mixes) / len(mixes)
        print()

    print("Average combined score per group:")
    for group, avg in averages.items():
        print(f"  {group:14} {avg:.3f}")
    gap = averages["AI_CLEAR"] - (
        sum(averages[g] for g in ("HUMAN_CASUAL", "HUMAN_PLAIN"))
        / 2
    )
    print(f"\nAI_CLEAR minus the human groups' average: {gap:.3f}")


if __name__ == "__main__":
    main()
