"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : modulos/algoritmos.py
Librerías : heapq, json, os, tempfile (biblioteca estándar de Python)
Propósito : Algoritmos de ordenamiento (interno y externo), búsqueda
            secuencial y TDA cola con prioridad.
            Se programan a mano (sin sorted()) para aplicar los
            contenidos de la unidad.
==============================================================================
"""

import heapq
import json
import os
import tempfile


# ------------------------------------------------------------------------------
# 1. ORDENAMIENTO INTERNO: QUICKSORT
# "Interno" = todos los datos caben y se ordenan en la memoria RAM.
# Se eligió Quicksort porque en promedio es O(n log n), más rápido que
# burbuja o inserción (O(n²)) cuando el historial crece.
# Idea: se elige un pivote y se separan los menores, iguales y mayores;
# luego se ordena cada parte de forma recursiva.
# ------------------------------------------------------------------------------
def quicksort(lista: list, clave, descendente: bool = False) -> list:
    if len(lista) <= 1:  # caso base: ya está ordenada
        return list(lista)
    pivote = clave(lista[len(lista) // 2])  # pivote = elemento central
    menores = [x for x in lista if clave(x) < pivote]
    iguales = [x for x in lista if clave(x) == pivote]
    mayores = [x for x in lista if clave(x) > pivote]
    if descendente:
        return (
            quicksort(mayores, clave, True) + iguales + quicksort(menores, clave, True)
        )
    return quicksort(menores, clave) + iguales + quicksort(mayores, clave)


# ------------------------------------------------------------------------------
# 2. ORDENAMIENTO EXTERNO: MEZCLA POR BLOQUES (external merge sort)
# "Externo" = se usa cuando el historial es tan grande que no cabe en memoria.
# Fase 1: se divide en bloques pequeños, cada bloque se ordena en memoria
#         (quicksort) y se guarda en un ARCHIVO temporal en disco.
# Fase 2: se mezclan los archivos leyendo línea por línea (mezcla de k vías),
#         sin cargar todo a la vez.
# ------------------------------------------------------------------------------
def ordenamiento_externo(
    registros: list, clave, descendente: bool = False, tam_bloque: int = 20
) -> list:
    archivos = []
    try:
        # Fase 1: bloques ordenados escritos en disco (una línea JSON por registro)
        for i in range(0, len(registros), tam_bloque):
            bloque = quicksort(registros[i : i + tam_bloque], clave, descendente)
            tmp = tempfile.NamedTemporaryFile(
                "w", suffix=".jsonl", delete=False, encoding="utf-8"
            )
            with tmp:
                for registro in bloque:
                    tmp.write(json.dumps(registro, default=str) + "\n")
            archivos.append(tmp.name)

        # Fase 2: mezcla de k vías. heapq.merge toma siempre el menor (o mayor)
        # de los primeros elementos de cada archivo.
        lectores = [open(nombre, encoding="utf-8") for nombre in archivos]
        try:
            flujos = [(json.loads(linea) for linea in lector) for lector in lectores]
            return list(heapq.merge(*flujos, key=clave, reverse=descendente))
        finally:
            for lector in lectores:
                lector.close()
    finally:
        for nombre in archivos:  # se borran los archivos temporales
            os.remove(nombre)


# ------------------------------------------------------------------------------
# 3. BÚSQUEDA SECUENCIAL
# Recorre la lista elemento por elemento hasta encontrar el valor buscado.
# Es O(n), pero no exige que la lista esté ordenada; para catálogos chicos
# (10 ingredientes, pocos usuarios) es simple y suficiente.
# Se usa para validar el usuario en el login y para consultar insumos.
# ------------------------------------------------------------------------------
def busqueda_secuencial(lista: list, clave, valor):
    for elemento in lista:
        if clave(elemento) == valor:
            return elemento  # se detiene en la primera coincidencia
    return None  # no se encontró


# ------------------------------------------------------------------------------
# 4. TDA COLA CON PRIORIDAD
# Sale primero el elemento con MAYOR prioridad (no el primero que llegó).
# Se usa para jerarquizar qué menús o ingredientes generan más pérdida.
# heapq implementa un montículo de mínimos; por eso se guarda la prioridad
# con signo negativo, para que salga primero la mayor.
# ------------------------------------------------------------------------------
class ColaPrioridad:
    def __init__(self):
        self._monticulo = []
        self._contador = 0  # desempata elementos con igual prioridad

    def encolar(self, prioridad: float, elemento):
        heapq.heappush(self._monticulo, (-prioridad, self._contador, elemento))
        self._contador += 1

    def desencolar(self):
        """Devuelve (prioridad, elemento) con la mayor prioridad."""
        prioridad, _, elemento = heapq.heappop(self._monticulo)
        return -prioridad, elemento

    def esta_vacia(self) -> bool:
        return not self._monticulo


# ------------------------------------------------------------------------------
# Prueba rápida (python -m modulos.algoritmos)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    datos = [
        {"menu": "A", "perdida": 3350},
        {"menu": "B", "perdida": 1050},
        {"menu": "C", "perdida": 4200},
        {"menu": "D", "perdida": 0},
        {"menu": "E", "perdida": 2250},
    ]
    perdida = lambda r: r["perdida"]
    print("Quicksort desc :", [r["menu"] for r in quicksort(datos, perdida, True)])
    print(
        "Externo (bloques de 2):",
        [r["menu"] for r in ordenamiento_externo(datos, perdida, True, 2)],
    )
    print("Búsqueda 'E'   :", busqueda_secuencial(datos, lambda r: r["menu"], "E"))
    cola = ColaPrioridad()
    for r in datos:
        cola.encolar(r["perdida"], r["menu"])
    print("Mayor pérdida  :", cola.desencolar())
