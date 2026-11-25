from collections import Counter
from fractions import Fraction


class JointEstimator:
    def __init__(self, frequencies, max_pairs):
        self.population = sum(frequencies.values())
        self.mass, self.slot = Counter(), Counter()
        for (mass, slot), count in frequencies.items():
            self.mass[mass] += count
            self.slot[slot] += count
        biggest = sorted(frequencies, key=lambda pair: (-frequencies[pair], pair))[:max_pairs]
        self.common = {pair: Fraction(frequencies[pair], self.population) for pair in biggest}
        self.remaining_joint = 1 - sum(self.common.values())
        self.remaining_independent = 1 - sum(self.independent(*pair) for pair in self.common)

    def independent(self, mass, slot):
        return Fraction(self.mass[mass] * self.slot[slot], self.population ** 2)

    def joint(self, mass, slot):
        if (mass, slot) in self.common:
            return self.common[(mass, slot)]
        if not self.remaining_independent:
            return Fraction(0)
        return self.independent(mass, slot) * self.remaining_joint / self.remaining_independent


def q_error(predicted, actual):
    left, right = max(1, predicted), max(1, actual)
    return max(left / right, right / left)
