"""
Optimisation d'un inverseur CMOS par algorithme MIDACO (colonie de fourmis)
Utilise le fichier perf_cmos_inverter.py pour le calcul des performances.

"""

import sys
from Midaco import midaco
from perf_cmos_inverter import compute_performances, compute_performances_for_optim

# Clé MIDACO (version limitée)
KEY = b'MIDACO_LIMITED_VERSION___[CREATIVE_COMMONS_BY-NC-ND_LICENSE]'

# Définition du problème
problem = {}
option = {}

problem['@'] = compute_performances_for_optim

# Dimensions
problem['o'] = 1   # 1 objectif
problem['n'] = 3   # 3 variables: Wn, Wp, L
problem['ni'] = 0  # variables continues
problem['m'] = 2   # 2 contraintes (ratio Wp/Wn)
problem['me'] = 0  # 0 contraintes d'égalité

# Bornes (Wn, Wp en µm, L en µm)
problem['xl'] = [0.5, 0.5, 0.35]   # Wn_min, Wp_min, L_min
problem['xu'] = [50.0, 150.0, 1.0]  # Wn_max, Wp_max, L_max

# Point de départ
problem['x'] = [2.0, 6.0, 0.35]

# Options MIDACO
option['maxeval'] = 5000
option['maxtime'] = 60 * 5
option['printeval'] = 500
option['save2file'] = 1
option['parallel'] = 0

# Paramètres par défaut
for i in range(1, 14):
    option['param' + str(i)] = 0.0


def run_optimization():
    """Lance l'optimisation MIDACO."""
    print("=" * 60)
    print("Optimisation inverseur CMOS - MIDACO")
    print("Variables: Wn, Wp, L (µm)")
    print("Objectif: minimiser delay + 0.01*power + 0.001*area")
    print("=" * 60)
    solution = midaco.run(problem, option, KEY)
    return solution


if __name__ == '__main__':
    solution = run_optimization()

    Wn, Wp, L = solution['x'][0], solution['x'][1], solution['x'][2]
    perf = compute_performances(Wn, Wp, L)

    print("\n" + "=" * 60)
    print("Solution optimisée : ")
    print("=" * 60)
    print("Dimensions: Wn = {:.2f} µm, Wp = {:.2f} µm, L = {:.3f} µm".format(Wn, Wp, L))
    print("Performances:")
    print("  Delay:     {:.3f} ns".format(perf['delay'] * 1e9))
    print("  P_dyn:     {:.3f} µW".format(perf['power_dyn'] * 1e6))
    print("  P_stat:    {:.6f} µW".format(perf['power_stat'] * 1e6))
    print("  Surface:   {:.2f} µm²".format(perf['area']))
    print("Valeur objectif: {:.6f}".format(solution['f'][0]))
