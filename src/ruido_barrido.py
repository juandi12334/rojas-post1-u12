"""Experimento extra: como cae la probabilidad de exito de Grover |11>
al subir el error de 2 qubits y al agregar profundidad al circuito."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from grover_noise import build_grover_circuit, build_noise_model

SHOTS = 8192
TARGET = "11"


def prob_exito(qc, p1q, p2q):
    sim = AerSimulator(noise_model=build_noise_model(p1q, p2q), seed_simulator=12)
    counts = sim.run(qc, shots=SHOTS).result().get_counts()
    return counts.get(TARGET, 0) / SHOTS


def grover_con_relleno(pares_cz):
    """Grover de 1 iteracion con 'pares_cz' pares de CZ consecutivos antes de medir.
    Dos CZ seguidos son la identidad, asi que sin ruido el resultado no cambia,
    pero cada CZ agrega una puerta ruidosa (simula un circuito mas profundo)."""
    qc = QuantumCircuit(2, 2)
    qc.h([0, 1])
    qc.cz(0, 1)
    qc.h([0, 1]); qc.x([0, 1]); qc.cz(0, 1); qc.x([0, 1]); qc.h([0, 1])
    for _ in range(pares_cz):
        qc.cz(0, 1)
        qc.cz(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


if __name__ == "__main__":
    os.makedirs("capturas", exist_ok=True)

    print("A) Barrido de la tasa de error de 2 qubits (p1q = 0.1%)")
    tasas = [0.0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15]
    base = build_grover_circuit(TARGET)
    p_barrido = []
    for p2q in tasas:
        p = prob_exito(base, 0.001, p2q)
        p_barrido.append(p)
        print(f"  p2q = {p2q * 100:5.1f}%  ->  exito |{TARGET}> = {p * 100:5.1f}%")

    print("\nB) Profundidad creciente con p2q = 1% (cada par agrega 2 CZ)")
    pares = [0, 1, 2, 5, 10, 20, 40, 80]
    p_prof = []
    for k in pares:
        p = prob_exito(grover_con_relleno(k), 0.001, 0.01)
        p_prof.append(p)
        print(f"  CZ totales = {2 + 2 * k:3d}  ->  exito |{TARGET}> = {p * 100:5.1f}%")
    print("  (con ruido total, 4 estados equiprobables darian 25.0%)")

    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    axs[0].plot([t * 100 for t in tasas], [p * 100 for p in p_barrido], "o-")
    axs[0].set_xlabel("Error de puerta de 2 qubits (%)")
    axs[0].set_ylabel("P(exito) de |11> (%)")
    axs[0].set_title("Barrido de la tasa de error")
    axs[0].axhline(25, color="gray", ls="--", label="azar (25%)")
    axs[0].legend(); axs[0].grid(alpha=0.3)
    axs[1].plot([2 + 2 * k for k in pares], [p * 100 for p in p_prof], "o-")
    axs[1].set_xlabel("Numero de puertas CZ en el circuito")
    axs[1].set_ylabel("P(exito) de |11> (%)")
    axs[1].set_title("Profundidad creciente (p2q = 1%)")
    axs[1].axhline(25, color="gray", ls="--", label="azar (25%)")
    axs[1].legend(); axs[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("capturas/ruido_barrido.png", dpi=150)
