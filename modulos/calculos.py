"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : modulos/calculos.py
Librerías : math (biblioteca estándar de Python)
Propósito : Motor de cálculo: insumos indivisibles, merma, pérdida,
            costo por plato y precio de venta.
==============================================================================
REGLAS (definidas en clase)
1. Todo se mide en PORCIONES. Cada unidad de compra rinde "porciones_unidad"
   porciones (utilidad de la tabla: 1 kg tomate = 4, 1 lechuga = 10, etc.).
2. La receta indica cuántas porciones de cada ingrediente usa para 4 comensales.
   Se escalan a los comensales pedidos y se REDONDEAN HACIA ARRIBA
   (3,2 tomates = 4 tomates):
       porciones_usadas = ceil(porciones_receta × comensales / 4)
3. Productos indivisibles y no almacenables: se compra el entero superior
       unidades = ceil(porciones_usadas / porciones_unidad)
   y todo lo que sobra es merma:
       merma = unidades × porciones_unidad − porciones_usadas
4. pérdida = merma / porciones_unidad × costo
   costo por plato = costo total / comensales ; precio = costo por plato × 1,25
==============================================================================
"""

import math

from modulos.modelos import DetalleOrden, Orden, Receta

MARGEN_GANANCIA = 0.25  # 25 % de ganancia sobre el costo


def calcular_orden(receta: Receta, comensales: int) -> Orden:
    """Calcula compras, mermas y costos de una receta para N comensales."""
    # Validación: no se aceptan valores nulos, negativos ni cero
    if not isinstance(comensales, int) or comensales <= 0:
        raise ValueError("La cantidad de comensales debe ser un entero mayor que cero.")
    # Una receta sin ingredientes indicaría un error de carga en la base de datos
    if not receta.items:
        raise ValueError(
            f"La receta '{receta.nombre}' no tiene ingredientes registrados."
        )

    detalle = []
    for item in receta.items:
        ing = item.ingrediente

        # 1) Porciones a usar, proporcionales a los comensales y redondeadas
        #    hacia arriba. Se redondea a 9 decimales ANTES de math.ceil para
        #    evitar errores de punto flotante (2.0000000000000004 -> 3).
        porciones_usadas = math.ceil(
            round(item.porciones * comensales / receta.base_comensales, 9)
        )

        # 2) Unidades de compra enteras (no se puede comprar media lechuga)
        unidades = math.ceil(porciones_usadas / ing.porciones_unidad)

        # 3) Merma física: porciones compradas que no se usan
        merma = unidades * ing.porciones_unidad - porciones_usadas

        # 4) Costo de lo comprado y valor de la merma (fracción no usada × costo)
        costo = unidades * ing.costo
        perdida = merma / ing.porciones_unidad * ing.costo

        detalle.append(
            DetalleOrden(
                ing,
                porciones_usadas,
                unidades,
                merma,
                round(costo, 2),
                round(perdida, 2),
            )
        )

    costo_total = sum(d.costo for d in detalle)
    costo_por_plato = costo_total / comensales
    precio_venta = costo_por_plato * (1 + MARGEN_GANANCIA)
    perdida_merma = sum(d.perdida for d in detalle)

    return Orden(
        receta,
        comensales,
        detalle,
        round(costo_total, 2),
        round(costo_por_plato, 2),
        round(precio_venta, 2),
        round(perdida_merma, 2),
    )


# ------------------------------------------------------------------------------
# Prueba rápida del motor (solo se ejecuta con: python -m modulos.calculos)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    from modulos.modelos import Ingrediente, ItemReceta

    tomate = Ingrediente(6, "Tomate", 1500, "kg", 4)
    pollo = Ingrediente(3, "Tuto de pollo", 1200, "unidad", 1)
    cebolla = Ingrediente(1, "Cebolla", 500, "unidad", 4)
    aceite = Ingrediente(10, "Aceite", 1000, "litro", 10)
    salteado = Receta(
        5,
        "Pollo Salteado con Verduras",
        4,
        [
            ItemReceta(pollo, 4),
            ItemReceta(tomate, 3),
            ItemReceta(cebolla, 4),
            ItemReceta(aceite, 4),
        ],
    )

    for n in (4, 5):
        orden = calcular_orden(salteado, n)
        print(f"{orden.receta.nombre} · {orden.comensales} comensales")
        for d in orden.detalle:
            print(
                f"  {d.ingrediente.nombre:13} usa {d.porciones_usadas:2} porc. | compra {d.unidades} "
                f"{d.ingrediente.unidad_compra:7} | merma {d.merma} porc. | pérdida ${d.perdida:,.0f}"
            )
        print(
            f"  Costo total ${orden.costo_total:,.0f} | por plato ${orden.costo_por_plato:,.0f} | "
            f"venta ${orden.precio_venta:,.0f} | pérdida ${orden.perdida_merma:,.0f}"
        )
