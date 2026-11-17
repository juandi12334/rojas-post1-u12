"""Estado de Bell |Phi+> = (|00> + |11>)/sqrt(2) con Qiskit y AerSimulator."""
import os
import matplotlib
matplotlib.use("Agg")  # sin ventana, solo guardamos la imagen
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram


def bell_state_experiment(shots=1024):
    """Prepara el estado de Bell y lo mide."""
    qc = QuantumCircuit(2, 2)      # 2 qubits y 2 bits clasicos

    qc.h(0)                        # superposicion en el qubit 0
    qc.cx(0, 1)                    # CNOT: entrelaza el qubit 1 con el 0
    qc.measure([0, 1], [0, 1])

    simulator = AerSimulator()
    counts = simulator.run(qc, shots=shots).result().get_counts()

    print(f"Resultados Bell |Phi+> ({shots} shots):")
    for state, count in sorted(counts.items()):
        print(f"  |{state}> : {count:4d} ({count / shots * 100:.1f}%)")

    # Solo pueden aparecer 00 y 11
    assert "01" not in counts and "10" not in counts, \
        "ERROR: aparecieron estados no entrelazados"
    print("OK: correlacion perfecta verificada")

    os.makedirs("capturas", exist_ok=True)
    fig = plot_histogram(counts, title="Estado de Bell |Phi+> (1024 shots)")
    fig.savefig("capturas/bell_histogram.png", dpi=150)

    print("Circuito:")
    print(qc.draw(output="text"))
    return counts


if __name__ == "__main__":
    bell_state_experiment()
