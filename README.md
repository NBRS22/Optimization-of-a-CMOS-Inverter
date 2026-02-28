# Optimisation inverseur CMOS

**Auteurs** : Nour EL Bachari, Asmae HMIDANI

Projet d'optimisation des dimensions d'un inverseur CMOS en technologie AMS 0.35µm. La méthode combine un **modèle analytique** des performances (délai, consommation, surface) et l'algorithme **MIDACO** (colonie de fourmis) pour trouver les dimensions optimales (Wn, Wp, L). Les résultats sont validés par simulation **LTSpice**.

## Prérequis

- Python 3.8+
- **NumPy**
- **LTspice** (pour les simulations manuelles)
- **PyLTSpice** (pour les boucles d'optimisation)

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

| Commande | Description |
|----------|-------------|
| `python optimize_inverter.py` | Lance l'optimisation MIDACO. Utilise le modèle analytique pour évaluer les performances. Affiche la solution optimale (Wn, Wp, L) et les performances associées. |
| `python perf_cmos_inverter.py` | Teste le calcul des performances pour des dimensions typiques (Wn=2µm, Wp=6µm, L=0.35µm). Affiche délai, puissance et surface. |
| `python optimize_inverter_ltspice.py` | Boucle d'optimisation qui appelle LTSpice pour chaque évaluation. Recherche par grille sur Wn et Wp. Nécessite LTspice et PyLTSpice. |

## Simulation LTSpice

- **Schéma** : ouvrir `TP.asc` dans LTspice. Les paramètres Wn, Wp, L sont dans la directive `.param`.
- **Netlist** : `inverter_cmos.cir` peut être simulé directement. Modifier les valeurs dans `.param` pour tester d'autres dimensions.

## Structure du projet

| Fichier | Rôle |
|---------|------|
| `perf_cmos_inverter.py` | Calcule délai, puissance et surface à partir de formules analytiques (modèle RC, équations MOSFET). Interface pour MIDACO. |
| `optimize_inverter.py` | Configure et lance l'optimisation MIDACO. Minimise un objectif composite (délai + 0.01×puissance + 0.001×surface). |
| `Midaco/` | Package MIDACO : interface Python (`midaco.py`), bibliothèque native (`midacopy.dll`).|
| `inverter_cmos.cir` | Netlist SPICE paramétrée. Inclut `5827_035.lib`, source PULSE, transistors NM/PM, mesures tphl/tplh. |
| `TP.asc` | Schéma LTSpice de l'inverseur avec paramètres symboliques. |
| `5827_035.lib` | Bibliothèque technologique AMS 0.35µm (modèles NMOS, PMOS). |

## Rapport

Le rapport décrivant la méthodologie et les résultats est fourni en **PDF** dans le dossier rapport.

## Références

- [MIDACO Solver](http://www.midaco-solver.com/) — Algorithme d'optimisation par colonie de fourmis
- [PyLTSpice](https://pypi.org/project/PyLTSpice/) — Pilotage de LTSpice depuis Python
