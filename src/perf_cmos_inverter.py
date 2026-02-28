"""
Fichier de calcul des performances d'un inverseur CMOS
Technologie AMS 0.35µm (5827_035.lib)

Performances calculées:
- Vitesse (propagation delay): tp [s]
- Consommation: P_dyn [W] + P_stat [W]
- Surface: Area [µm²]

Variables de conception:
- Wn: largeur du transistor NMOS [µm]
- Wp: largeur du transistor PMOS [µm]
- L: longueur du canal [µm] (typiquement Lmin=0.35µm)

"""

import math

# Constantes du process AMS 0.35µm (extrait de 5827_035.lib)
VDD = 3.3          # Tension d'alimentation [V]
VTH_N = 0.498      # Seuil NMOS [V]
VTH_P = 0.6915     # Seuil PMOS [V]
U0_N = 475.8       # Mobilité NMOS [cm²/Vs]
U0_P = 148.2       # Mobilité PMOS [cm²/Vs]
TOX = 7.575e-9     # Épaisseur oxyde [m]
EPS_OX = 3.9 * 8.85e-12  # Permittivité SiO2 [F/m]
COX = EPS_OX / TOX        # Capacité oxyde par unité de surface [F/m²]

# Conversion mobilité: cm²/Vs -> m²/Vs
MU_N = U0_N * 1e-4
MU_P = U0_P * 1e-4

# k' = mu * Cox [A/V²]
KPRIME_N = MU_N * COX
KPRIME_P = MU_P * COX

# Capacité de charge typique (entrée d'un inverseur suivant)
CL = 10e-15  # 10 fF
# Fréquence de commutation pour calcul consommation dynamique
F_CLK = 100e6  # 100 MHz

# Facteur 0.69 pour delay RC (réponse à 50% de Vdd)
ALPHA_DELAY = 0.69


def compute_performances(Wn, Wp, L):
    """
    Calcule les performances d'un inverseur CMOS.

    Paramètres:
    -----------
    Wn : float - Largeur NMOS [µm]
    Wp : float - Largeur PMOS [µm]
    L  : float - Longueur canal [µm]

    Retourne:
    ---------
    dict avec: delay [s], power_dyn [W], power_stat [W], area [µm²]
    
    """
    Wn_m = Wn * 1e-6
    Wp_m = Wp * 1e-6
    L_m = L * 1e-6

    # --- Vitesse (propagation delay) ---
    # Modèle RC: tp = 0.69 * R_eq * C_L
    # R_n ≈ 1 / (k'n * (Wn/L) * (Vdd-Vth_n)) en saturation
    # On utilise le chemin critique (NMOS pour discharge)
    VOD_N = VDD - VTH_N
    VOD_P = VDD - VTH_P

    R_n = 1.0 / (KPRIME_N * (Wn_m / L_m) * VOD_N) if Wn_m > 0 else 1e12
    R_p = 1.0 / (KPRIME_P * (Wp_m / L_m) * VOD_P) if Wp_m > 0 else 1e12

    # Delay moyen (moyenne rise et fall)
    tp_n = ALPHA_DELAY * R_n * CL
    tp_p = ALPHA_DELAY * R_p * CL
    tp = (tp_n + tp_p) / 2.0

    # --- Consommation ---
    # Dynamique: P_dyn = C_L * Vdd² * f
    P_dyn = CL * (VDD ** 2) * F_CLK

    # Statique (sous-seuil, approximation): I_leak ~ 10nA
    I_LEAK = 10e-9
    P_stat = I_LEAK * VDD

    # --- Surface ---
    # Surface active = W*L pour chaque transistor + zones de diffusion
    # Approximation: Area ≈ (Wn + Wp) * L * facteur_layout
    FACTOR_LAYOUT = 3.0 
    area_um2 = (Wn + Wp) * L * FACTOR_LAYOUT

    return {
        'delay': tp,
        'power_dyn': P_dyn,
        'power_stat': P_stat,
        'power_total': P_dyn + P_stat,
        'area': area_um2,
    }


def compute_performances_for_optim(x):
    """
    Interface pour MIDACO: x = [Wn, Wp, L]
    Retourne (f, g) pour minimisation.

    """
    Wn, Wp, L = x[0], x[1], x[2]
    perf = compute_performances(Wn, Wp, L)

    # Objectif: minimiser une combinaison pondérée
    # Minimiser: w1*delay + w2*power + w3*area
    f_delay = perf['delay'] * 1e9   # en ns
    f_power = perf['power_total'] * 1e6  # en µW
    f_area = perf['area']
    w1, w2, w3 = 1.0, 0.01, 0.001
    f = w1 * f_delay + w2 * f_power + w3 * f_area

    # Contraintes: g >= 0 (les bornes xl/xu gèrent déjà Wn, Wp, L)
    # Contrainte ratio Wp/Wn pour seuil symétrique: 1.5 <= Wp/Wn <= 4
    ratio = Wp / Wn if Wn > 0.01 else 1.0
    g = [
        ratio - 1.2,   # Wp/Wn >= 1.2
        4.5 - ratio,   # Wp/Wn <= 4.5
    ]

    return [f], g


if __name__ == '__main__':
    Wn, Wp, L = 2.0, 6.0, 0.35
    perf = compute_performances(Wn, Wp, L)
    print("Performances inverseur CMOS (Wn={}, Wp={}, L={} µm) : ".format(Wn, Wp, L))
    print("  Delay:     {:.3f} ns".format(perf['delay'] * 1e9))
    print("  P_dyn:     {:.3f} µW".format(perf['power_dyn'] * 1e6))
    print("  P_stat:    {:.6f} µW".format(perf['power_stat'] * 1e6))
    print("  Surface:   {:.2f} µm²".format(perf['area']))
