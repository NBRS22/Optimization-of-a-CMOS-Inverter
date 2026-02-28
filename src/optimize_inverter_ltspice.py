"""
Boucle d'optimisation avec appel direct au simulateur LTSpice
Utilise PyLTSpice pour lancer des simulations et extraire les performances au lieu du fichier de calcul analytique.

"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Vérifier que spicelib est disponible
try:
    from spicelib.editor.spice_editor import SpiceEditor
    from spicelib.sim.sim_runner import SimRunner
    from spicelib.simulators.ltspice_simulator import LTspice
    from spicelib.log.ltsteps import LTSpiceLogReader
    SPICELIB_AVAILABLE = True
except ImportError:
    SPICELIB_AVAILABLE = False

# Répertoires projet
LTSPICE_DIR = PROJECT_ROOT / "ltspice"


def run_simulation_and_extract_delay(Wn_um, Wp_um, L_um):
    """
    Lance une simulation LTSpice avec les dimensions données et extrait le delay.

    Paramètres:
    -----------
    Wn_um, Wp_um, L_um : dimensions en µm

    Retourne:
    ---------
    dict avec delay_ns, tphl, tplh, success
    
    """
    if not SPICELIB_AVAILABLE:
        return {'success': False, 'delay_ns': 1e6, 'tphl': 1e6, 'tplh': 1e6}

    # Convertir en notation SPICE (ex: 2.0 -> "2u")
    Wn_str = f"{Wn_um:.2f}u" if Wn_um >= 1 else f"{Wn_um*1000:.0f}n"
    Wp_str = f"{Wp_um:.2f}u" if Wp_um >= 1 else f"{Wp_um*1000:.0f}n"
    L_str = f"{L_um:.3f}u" if L_um >= 0.1 else f"{L_um*1000:.0f}n"

    cir_file = LTSPICE_DIR / "inverter_cmos.cir"
    if not cir_file.exists():
        return {'success': False, 'delay_ns': 1e6, 'tphl': 1e6, 'tplh': 1e6}

    try:
        editor = SpiceEditor(cir_file)
        editor.set_parameter("Wn", Wn_str)
        editor.set_parameter("Wp", Wp_str)
        editor.set_parameter("L", L_str)

        runner = SimRunner(
            simulator=LTspice,
            parallel_sims=1,
            timeout=120,
            output_folder=LTSPICE_DIR / "sim_output",
            cwd=LTSPICE_DIR,
        )
        runner.run(editor, wait_resource=True)
        runner.wait_completion(timeout=130)

        if runner.failSim > 0 or len(runner.completed_tasks) == 0:
            return {'success': False, 'delay_ns': 1e6, 'tphl': 1e6, 'tplh': 1e6}

        task = runner.completed_tasks[-1]
        log_file = task.log_file

        if log_file is None or not Path(log_file).exists():
            return {'success': False, 'delay_ns': 1e6, 'tphl': 1e6, 'tplh': 1e6}

        tphl, tplh = None, None
        try:
            log = LTSpiceLogReader(str(log_file))
            tphl = log.get_measure_value("tphl")
            tplh = log.get_measure_value("tplh")
        except Exception:
            # Fallback: parse log file directly (format LTspice)
            import re
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            m_phl = re.search(r'tphl\s*=\s*([\d.eE+-]+)', content)
            m_plh = re.search(r'tplh\s*=\s*([\d.eE+-]+)', content)
            if m_phl:
                tphl = float(m_phl.group(1))
            if m_plh:
                tplh = float(m_plh.group(1))

        if tphl is None:
            tphl = 1e-6
        if tplh is None:
            tplh = 1e-6

        tpd = (float(tphl) + float(tplh)) / 2.0
        delay_ns = tpd * 1e9

        return {
            'success': True,
            'delay_ns': delay_ns,
            'tphl': float(tphl) * 1e9,
            'tplh': float(tplh) * 1e9,
        }
    except Exception as e:
        print(f"Erreur simulation: {e}")
        return {'success': False, 'delay_ns': 1e6, 'tphl': 1e6, 'tplh': 1e6}


def optimize_with_simulator():
    """
    Boucle d'optimisation simple (recherche par grille réduite)
    utilisant le simulateur LTSpice pour évaluer les performances.

    """
    if not SPICELIB_AVAILABLE:
        print("PyLTSpice/spicelib non installé. Exécutez: pip install PyLTSpice")
        return

    # S'assurer que la bibliothèque techno est dans sim_output (pour .include)
    import shutil
    sim_out = LTSPICE_DIR / "sim_output"
    sim_out.mkdir(exist_ok=True)
    lib_src = LTSPICE_DIR / "5827_035.lib"
    lib_dst = sim_out / "5827_035.lib"
    if lib_src.exists() and (not lib_dst.exists() or lib_src.stat().st_mtime > lib_dst.stat().st_mtime):
        shutil.copy2(lib_src, lib_dst)

    print("=" * 60)
    print("Optimisation inverseur CMOS via LTSpice")
    print("=" * 60)

    # Grille de recherche réduite (pour limiter le nombre de simulations)
    Wn_values = [1.0, 2.0, 3.0]
    Wp_values = [3.0, 6.0, 9.0]
    L_val = 0.35

    best_delay = 1e9
    best_params = None

    for Wn in Wn_values:
        for Wp in Wp_values:
            if Wp / Wn < 1.2 or Wp / Wn > 4.5:
                continue
            print(f"  Simulation Wn={Wn}µm, Wp={Wp}µm, L={L_val}µm...", end=" ")
            result = run_simulation_and_extract_delay(Wn, Wp, L_val)
            if result['success']:
                print(f"tpd={result['delay_ns']:.2f} ns")
                if result['delay_ns'] < best_delay:
                    best_delay = result['delay_ns']
                    best_params = (Wn, Wp, L_val)
            else:
                print("ÉCHEC")

    print("\n" + "=" * 60)
    if best_params:
        print("Meilleure solution trouvée:")
        print(f"  Wn={best_params[0]} µm, Wp={best_params[1]} µm, L={best_params[2]} µm")
        print(f"  Delay moyen (LTSpice): {best_delay:.2f} ns")
        # Calcul surface et puissance pour comparaison
        try:
            from perf_cmos_inverter import compute_performances
            perf = compute_performances(best_params[0], best_params[1], best_params[2])
            print(f"  Surface (analytique): {perf['area']:.2f} µm²")
            print(f"  P_dyn (analytique): {perf['power_dyn']*1e6:.2f} µW")
        except ImportError:
            pass
        # Sauvegarder pour le rapport
        results_file = PROJECT_ROOT / "ltspice_optim_results.txt"
        with open(results_file, 'w') as f:
            f.write(f"Wn={best_params[0]}\nWp={best_params[1]}\nL={best_params[2]}\n")
            f.write(f"tpd_ns={best_delay:.3f}\n")
    else:
        print("Aucune simulation réussie. Vérifiez que LTspice est installé.")
    print("=" * 60)


if __name__ == '__main__':
    optimize_with_simulator()
