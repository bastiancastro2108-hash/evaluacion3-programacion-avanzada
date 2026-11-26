"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : modulos/modelos.py
Librerías : dataclasses (biblioteca estándar de Python)
Propósito : Clases y TDA (Tipos de Datos Abstractos) que modelan los
            ingredientes, las recetas y las órdenes de servicio.
==============================================================================
"""

from dataclasses import dataclass, field


# ------------------------------------------------------------------------------
# CLASES DEL DOMINIO
# Se usan dataclasses porque generan automáticamente el constructor (__init__)
# y la representación del objeto, dejando el código más corto y legible.
# ------------------------------------------------------------------------------
@dataclass
class Ingrediente:
    """Producto que se compra. El costo es por UNIDAD DE COMPRA (kg, paquete, etc.)."""

    id: int
    nombre: str
    costo: int
    unidad_compra: str  # unidad, paquete, kg, litro, empaque
    porciones_unidad: int  # porciones que rinde 1 unidad de compra (1 kg tomate = 4)


@dataclass
class ItemReceta:
    """Un ingrediente dentro de una receta, con sus porciones para la base de comensales."""

    ingrediente: Ingrediente
    porciones: int


@dataclass
class Receta:
    """Menú. Sus ingredientes se guardan en un TDA LISTA (orden de la receta)."""

    id: int
    nombre: str
    base_comensales: int
    items: list = field(default_factory=list)  # lista de ItemReceta


@dataclass
class DetalleOrden:
    """Resultado del cálculo para UN ingrediente de una orden."""

    ingrediente: Ingrediente
    porciones_usadas: int  # porciones a usar (redondeadas hacia arriba)
    unidades: int  # unidades de compra enteras (productos indivisibles)
    merma: int  # porciones que sobran
    costo: float  # $ de lo comprado
    perdida: float  # $ que se pierde por la merma


@dataclass
class Orden:
    """Servicio solicitado por cocina con todos sus cálculos."""

    receta: Receta
    comensales: int
    detalle: list  # lista de DetalleOrden
    costo_total: float
    costo_por_plato: float
    precio_venta: float  # por plato, con 25 % de ganancia
    perdida_merma: float


# ------------------------------------------------------------------------------
# TDA COLA (FIFO: First In, First Out)
# Las órdenes de cocina se atienden en el orden en que llegan: la primera
# orden registrada es la primera que se prepara. Por eso se eligió una cola
# y no una pila (que atendería primero la última orden).
# ------------------------------------------------------------------------------
class Cola:
    def __init__(self):
        self._elementos = []

    def encolar(self, elemento):
        """Agrega al final de la cola."""
        self._elementos.append(elemento)

    def desencolar(self):
        """Quita y devuelve el primero de la cola (None si está vacía)."""
        return None if self.esta_vacia() else self._elementos.pop(0)

    def retirar(self, elemento):
        """Operación extra: saca un elemento de cualquier posición.
        Permite atender una orden fuera de turno si se terminó antes."""
        self._elementos.remove(elemento)

    def frente(self):
        """Muestra el primero sin quitarlo."""
        return None if self.esta_vacia() else self._elementos[0]

    def esta_vacia(self) -> bool:
        return len(self._elementos) == 0

    def __len__(self) -> int:
        return len(self._elementos)

    def como_lista(self) -> list:
        """Copia de los elementos, para mostrarlos sin modificar la cola."""
        return list(self._elementos)
