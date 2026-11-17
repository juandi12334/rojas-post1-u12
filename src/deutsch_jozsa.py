"""Algoritmo de Deutsch-Jozsa para n = 2 qubits de entrada."""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def oracle_constante(n):
    """Oraculo constante f(x) = 0: no hace nada (el ancilla queda igual)."""
    return QuantumCircuit(n + 1)


def oracle_balanceada(n):
    """Oraculo balanceado: f(x) = x0 xor x1 ... xor x(n-1).
    Un CNOT de cada qubit de entrada hacia el ancilla."""
    qc = QuantumCircuit(n + 1)
    for i in range(n):
        qc.cx(i, n)
    return qc


def deutsch_jozsa(oracle_qc, n, shots=1024):
    """Ejecuta Deutsch-Jozsa con el oraculo dado y devuelve los counts."""
    qc = QuantumCircuit(n + 1, n)

    # Ancilla en |-> = H|1>
    qc.x(n)
    qc.h(range(n + 1))
    qc.barrier()

    qc.compose(oracle_qc, inplace=True)   # una sola llamada al oraculo
    qc.barrier()

    qc.h(range(n))                        # interferencia
    qc.measure(range(n), range(n))        # solo se miden las entradas

    sim = AerSimulator()
    return sim.run(qc, shots=shots).result().get_counts()


if __name__ == "__main__":
    n = 2
    counts_c = deutsch_jozsa(oracle_constante(n), n)
    print(f"Constante:  {counts_c}")    # esperado: {'00': 1024}

    counts_b = deutsch_jozsa(oracle_balanceada(n), n)
    print(f"Balanceada: {counts_b}")    # esperado: sin '00'

    assert "00" in counts_c and len(counts_c) == 1, "Error: oraculo constante"
    assert "00" not in counts_b, "Error: oraculo balanceado retorno 00"
    print("OK: Deutsch-Jozsa verifica correctamente")
