"""Grover (2 qubits) bajo un modelo de ruido despolarizante."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.visualization import plot_histogram

from grover import oraculo_fase, difusor
from qiskit import QuantumCircuit


def build_grover_circuit(target="11"):
    """Mismo circuito de Grover del paso 3 (se reutilizan oraculo y difusor)."""
    qc = QuantumCircuit(2, 2)
    qc.h([0, 1])
    oraculo_fase(qc, target)
    difusor(qc)
    qc.measure([0, 1], [0, 1])
    return qc


def build_noise_model(p1q=0.001, p2q=0.01):
    """Error despolarizante: p1q en puertas de 1 qubit (h, x) y p2q en las
    de 2 qubits (cz). Son ordenes de magnitud de procesadores superconductores."""
    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p1q, 1), ["h", "x"])
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p2q, 2), ["cz"])
    return noise_model


def grover_noise_experiment(target="11", shots=1024):
    qc = build_grover_circuit(target)

    # Linea base sin ruido
    counts_ideal = AerSimulator().run(qc, shots=shots).result().get_counts()

    # Misma ejecucion con ruido en cada puerta
    noisy_sim = AerSimulator(noise_model=build_noise_model())
    counts_noisy = noisy_sim.run(qc, shots=shots).result().get_counts()

    p_ideal = counts_ideal.get(target, 0) / shots
    p_noisy = counts_noisy.get(target, 0) / shots

    print(f"Grover |{target}> sin ruido: {p_ideal * 100:.1f}%")
    print(f"Grover |{target}> con ruido: {p_noisy * 100:.1f}%")
    print(f"Degradacion: {(p_ideal - p_noisy) * 100:.1f} puntos porcentuales")
    print("Conteos con ruido:", dict(sorted(counts_noisy.items())))

    os.makedirs("capturas", exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    plot_histogram(counts_ideal, ax=axs[0])
    plot_histogram(counts_noisy, ax=axs[1])
    axs[0].set_title("Sin ruido")
    axs[1].set_title("Con ruido (despolarizante)")
    for ax in axs:
        ax.set_ylim(0, shots * 1.15)   # misma escala para comparar
    fig.tight_layout()
    fig.savefig("capturas/grover_noise_comparison.png", dpi=150)

    return p_ideal, p_noisy


if __name__ == "__main__":
    grover_noise_experiment()
