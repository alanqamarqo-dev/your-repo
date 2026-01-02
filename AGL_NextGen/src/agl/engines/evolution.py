"""Simple Evolution Engine

Provides `evolve_thought_process` — a conservative, dependency-free
string-based genetic algorithm used as a signal-integrity / repair
utility. This implementation is intentionally small, deterministic
by default, and safe (no subprocess, no file writes, no code exec).

Intended usage: pass a list of noisy signal strings and a `target`
string (default: "genetic algo"). The engine will attempt to evolve
candidate strings toward the target and return the best repaired
string along with metadata.
"""
from __future__ import annotations

import random
import string
from typing import List, Dict, Any, Tuple


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein distance (iterative, memory efficient)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # ensure a is the shorter
    if len(a) > len(b):
        a, b = b, a
    previous = list(range(len(a) + 1))
    for i, cb in enumerate(b, start=1):
        current = [i]
        for j, ca in enumerate(a, start=1):
            insertions = previous[j] + 1
            deletions = current[j - 1] + 1
            substitutions = previous[j - 1] + (0 if ca == cb else 1)
            current.append(min(insertions, deletions, substitutions))
        previous = current
    return previous[-1]


def evolve_thought_process(noisy_signals: List[str], target: str = "genetic algo", max_generations: int = 200, pop_size: int = 60, mutation_rate: float = 0.12) -> Dict[str, Any]:
    """Evolve candidate strings toward `target`.

    Enhancements:
    - Accepts a single `target` string (or caller can iterate over multiple targets).
    - Returns an `evolution_history` snapshot with sampled generation states.
    - Performs conservative dynamic adaptation of `mutation_rate` and `pop_size`
      if fitness improvement stalls.

    Args:
        noisy_signals: list of observed noisy strings (used as seeds).
        target: desired stable string.
        max_generations: max GA generations to run.
        pop_size: population size.
        mutation_rate: probability of mutating each character.

    Returns:
        dict with keys: 'result', 'distance', 'generations', 'status', 'score', 'evolution_history'
    """
    try:
        # expand alphabet to include digits and underscore so targets like
        # 'stable_agi_signal' can be represented directly
        alphabet = string.ascii_lowercase + string.digits + " _"
        # normalize target to allowed chars
        target = ''.join(ch for ch in target.lower() if ch in alphabet)

        # Seed population from noisy signals (cleaned) and random noise
        seeds = []
        for s in noisy_signals or []:
            try:
                s2 = ''.join(ch.lower() for ch in str(s) if ch.lower() in alphabet)
                if s2:
                    seeds.append(s2)
            except Exception:
                continue

        # pad/trim function
        def normalize(s: str) -> str:
            s = ''.join(ch for ch in s.lower() if ch in alphabet)
            if len(s) < len(target):
                s = s + ''.join(random.choice(alphabet) for _ in range(len(target) - len(s)))
            return s[:len(target)]

        population = []
        # start with seeds
        for s in seeds:
            population.append(normalize(s))
        # fill up with random strings
        while len(population) < pop_size:
            population.append(''.join(random.choice(alphabet) for _ in range(len(target))))

        def fitness(s: str) -> float:
            # higher is better; invert distance
            d = _levenshtein(s, target)
            # map to [0, 1]
            return 1.0 - (d / max(len(target), 1))

        def mutate(s: str) -> str:
            arr = list(s)
            for i in range(len(arr)):
                if random.random() < mutation_rate:
                    arr[i] = random.choice(alphabet)
            return ''.join(arr)

        def crossover(a: str, b: str) -> str:
            # one-point crossover
            if len(a) != len(b):
                b = normalize(b)
                a = normalize(a)
            pt = random.randint(1, len(a) - 1) if len(a) > 1 else 0
            child = a[:pt] + b[pt:]
            return child

        best = None
        best_score = -1.0

        # track evolution history snapshots
        evolution_history: Dict[str, Any] = {}
        last_recorded_score = None
        stagnant_rounds = 0

        for gen in range(1, max_generations + 1):
            # evaluate
            scored = [(fitness(ind), ind) for ind in population]
            scored.sort(reverse=True, key=lambda x: x[0])
            top_score, top_ind = scored[0]
            if top_score > best_score:
                best_score = top_score
                best = top_ind

            # success threshold: exact match or sufficiently close
            if _levenshtein(best, target) == 0 or best_score >= 0.98:
                return {
                    'result': best,
                    'distance': _levenshtein(best, target),
                    'generations': gen,
                    'status': 'repaired' if _levenshtein(best, target) == 0 else 'approx_repaired',
                    'score': best_score,
                    'evolution_history': evolution_history
                }

            # record history at a few checkpoints
            if gen == 1 or gen == int(max_generations/2) or gen == max_generations or gen % 50 == 0:
                evolution_history[f'generation_{gen}'] = {
                    'fitness': float(top_score),
                    'best_signal': top_ind,
                }

            # dynamic adaptation: if no meaningful improvement, increase mutation/pop
            if last_recorded_score is None:
                last_recorded_score = top_score
                stagnant_rounds = 0
            else:
                if (top_score - last_recorded_score) < 0.01:
                    stagnant_rounds += 1
                else:
                    stagnant_rounds = 0
                    last_recorded_score = top_score

            if stagnant_rounds and stagnant_rounds % 20 == 0:
                # slowly increase diversity to escape plateaus
                mutation_rate = min(0.5, mutation_rate * 1.5)
                pop_size = min(200, pop_size + 20)
                # ensure population is refreshed to new size
                while len(population) < pop_size:
                    population.append(''.join(random.choice(alphabet) for _ in range(len(target))))

            # selection: top 20% retained
            retain_n = max(2, int(0.2 * pop_size))
            next_pop = [ind for _, ind in scored[:retain_n]]

            # fill rest by crossover of top 50%
            mating_pool = [ind for _, ind in scored[:max(2, int(0.5 * pop_size))]]
            while len(next_pop) < pop_size:
                a = random.choice(mating_pool)
                b = random.choice(mating_pool)
                child = crossover(a, b)
                child = mutate(child)
                next_pop.append(child)

            population = next_pop

        # timed out
        evolution_history[f'generation_{max_generations}'] = {
            'fitness': float(best_score),
            'best_signal': best
        }
        return {'result': best or '', 'distance': _levenshtein(best or '', target), 'generations': max_generations, 'status': 'max_generations_reached', 'score': best_score, 'evolution_history': evolution_history}

    except Exception as e:
        return {'result': '', 'distance': None, 'generations': 0, 'status': f'error:{e}'}
