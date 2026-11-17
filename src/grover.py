"""Algoritmo de Grover para 2 qubits (4 elementos, 1 iteracion)."""
import os
import matplotlib
matplotlib.use("Agg")
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram


def oraculo_fase(qc, target):
    """Marca el estado target con fase -1 usando un CZ.
    Para los otros estados se rodea el CZ con X en los qubits que valen 0.
    Qiskit usa orden little-endian: target[0] es el qubit 1 y target[1] el qubit 0."""
    for qubit, bit in enumerate(reversed(target)):
        if bit == "0":
            qc.x(qubit)
    qc.cz(0, 1)
    for qubit, bit in enumerate(reversed(target)):
        if bit == "0":
            qc.x(qubit)


def difusor(qc):
    """Inversion alrededor de la media: H X CZ X H."""
    qc.h([0, 1])
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])


def grover_2qubits(target="11", shots=1024):
    """Grover para n = 2 buscando el estado target."""
    qc = QuantumCircuit(2, 2)
    qc.h([0, 1])              # superposicion uniforme
    oraculo_fase(qc, target)
    difusor(qc)
    qc.measure([0, 1], [0, 1])

    counts = AerSimulator().run(qc, shots=shots).result().get_counts()

    print(f"Grover buscando |{target}> ({shots} shots):")
    for state, count in sorted(counts.items()):
        print(f"  |{state}>: {count:4d} ({count / shots * 100:.1f}%)")

    top = max(counts, key=counts.get)
    veredicto = "CORRECTO" if top == target else "ERROR"
    print(f"Estado mas probable: |{top}> - {veredicto}")

    os.makedirs("capturas", exist_ok=True)
    fig = plot_histogram(counts, title=f"Grover, objetivo |{target}>")
    fig.savefig(f"capturas/grover_{target}.png", dpi=150)
    return counts


if __name__ == "__main__":
    for t in ["00", "01", "10", "11"]:
        grover_2qubits(target=t)
        print()
