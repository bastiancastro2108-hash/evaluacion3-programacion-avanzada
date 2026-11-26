"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : modulos/vista_cocina.py
Librerías : streamlit, pandas
Propósito : Interfaz operativa del perfil COCINA. Solo muestra QUÉ y CUÁNTO
            preparar: no muestra costos, precios ni pérdidas por merma
            (aunque se calculan y se guardan para el administrador).
==============================================================================
"""

import pandas as pd
import streamlit as st

from modulos.algoritmos import busqueda_secuencial, quicksort
from modulos.basedatos import (
    cargar_ingredientes_orden,
    cargar_pendientes,
    cargar_recetas,
    guardar_orden,
    marcar_preparada,
)
from modulos.calculos import calcular_orden
from modulos.modelos import Cola

PLURALES = {
    "unidad": "unidades",
    "porción": "porciones",
    "paquete": "paquetes",
    "litro": "litros",
    "empaque": "empaques",
    "kg": "kg",
}


def _con_unidad(cantidad: int, unidad: str) -> str:
    """Escribe '1 litro', '3 porciones', '2 kg'... (singular o plural)."""
    return f"{cantidad} {unidad if cantidad == 1 else PLURALES.get(unidad, unidad)}"


def _tabla_ingredientes(filas: list, clave: str):
    """Tabla de preparación ordenable, con controles en español.
    filas: [{"nombre", "porciones", "unidades", "unidad_compra"}]
    Se usa st.table (tabla fija) en vez de st.dataframe para que no aparezca el
    menú en inglés de estadísticas; el orden lo controla el usuario con
    nuestro quicksort."""
    c1, c2 = st.columns(2)
    criterio = c1.selectbox(
        "Ordenar por",
        ["Ingrediente", "Porciones a usar", "Retirar de bodega"],
        key=f"criterio_{clave}",
    )
    sentido = c2.radio(
        "Sentido",
        ["Menor a mayor", "Mayor a menor"],
        horizontal=True,
        key=f"sentido_{clave}",
    )
    campo = {
        "Ingrediente": "nombre",
        "Porciones a usar": "porciones",
        "Retirar de bodega": "unidades",
    }[criterio]
    ordenadas = quicksort(
        filas, lambda f: f[campo], descendente=(sentido == "Mayor a menor")
    )
    tabla = pd.DataFrame(
        [
            {
                "Ingrediente": f["nombre"],
                "Porciones a usar": _con_unidad(f["porciones"], "porción"),
                "Retirar de bodega": _con_unidad(f["unidades"], f["unidad_compra"]),
            }
            for f in ordenadas
        ]
    )
    tabla.index = range(1, len(tabla) + 1)  # numeración desde 1
    st.table(tabla)


def mostrar(perfil: dict):
    st.header("👨‍🍳 Cocina · Orden de preparación")

    recetas = cargar_recetas()

    # -------------------- Formulario de solicitud de servicio --------------------
    with st.form("solicitud", clear_on_submit=True):
        receta = st.selectbox("Menú", recetas, format_func=lambda r: r.nombre)
        # Se usa text_input (y no number_input) para validar el texto exacto:
        # number_input convertía en silencio un decimal (2.5 -> 2).
        texto = st.text_input("Cantidad de comensales", placeholder="Ej: 12")
        enviar = st.form_submit_button("Generar orden", type="primary")

    if enviar:
        # Validación: solo enteros mayores que cero. isdigit() es True únicamente
        # si TODOS los caracteres son dígitos, así rechaza vacío, "2.5", "-3" y "abc".
        texto = texto.strip()
        if not texto.isdigit() or int(texto) == 0:
            st.error(
                "Ingrese un número ENTERO de comensales mayor que cero (sin decimales)."
            )
        else:
            try:
                orden = calcular_orden(receta, int(texto))
            except ValueError as error:  # ej: receta sin ingredientes
                st.error(str(error))
                st.stop()
            # Se guarda AUTOMÁTICAMENTE con todos los cálculos, en estado 'pendiente'
            id_orden = guardar_orden(orden, perfil["usuario"])
            st.session_state["ultima_orden"] = orden
            st.success(f"Orden N°{id_orden} registrada.")

    # -------------------- Orden de preparación (sin datos financieros) --------------------
    orden = st.session_state.get("ultima_orden")
    if orden:
        st.subheader(
            f"Última orden: {orden.receta.nombre} · {orden.comensales} comensales"
        )
        _tabla_ingredientes(
            [
                {
                    "nombre": d.ingrediente.nombre,
                    "porciones": d.porciones_usadas,
                    "unidades": d.unidades,
                    "unidad_compra": d.ingrediente.unidad_compra,
                }
                for d in orden.detalle
            ],
            "ultima",
        )
        st.caption(
            "Los productos se retiran enteros: no se pueden fraccionar ni guardar."
        )

    # -------------------- Cola de órdenes pendientes (FIFO) --------------------
    # Las pendientes se leen desde Supabase (no de la sesión), así siguen ahí al
    # cerrar sesión o al entrar con otro usuario. Se cargan en un TDA Cola en
    # orden de llegada: la primera que entró es la primera que se prepara.
    cola = Cola()
    for pendiente in cargar_pendientes():
        cola.encolar(pendiente)

    st.divider()
    st.subheader(f"Órdenes pendientes ({len(cola)})")
    if cola.esta_vacia():
        st.caption("No hay órdenes pendientes.")
        return

    # Opción 1 (FIFO): preparar la más antigua
    if st.button("✅ Preparar la siguiente en turno (FIFO)", type="primary"):
        primera = cola.desencolar()  # sale la que entró primero
        marcar_preparada(primera["id"])  # el cambio queda guardado en la base
        st.rerun()

    # Opción 2: marcar cualquier orden que se haya terminado antes
    for i, p in enumerate(cola.como_lista(), start=1):
        col_texto, col_boton = st.columns([5, 1])
        col_texto.write(
            f"{i}. Orden N°{p['id']} · {p['recetas']['nombre']} · {p['comensales']} comensales"
        )
        if col_boton.button("Preparada", key=f"preparar_{p['id']}"):
            # Se ubica la orden en la cola con búsqueda secuencial y se retira
            orden = busqueda_secuencial(cola.como_lista(), lambda x: x["id"], p["id"])
            cola.retirar(orden)
            marcar_preparada(orden["id"])
            st.rerun()
        # Los ingredientes de cada orden pendiente se pueden consultar en cualquier momento
        with st.expander(f"Ver ingredientes de la orden N°{p['id']}"):
            _tabla_ingredientes(
                [
                    {
                        "nombre": d["ingredientes"]["nombre"],
                        "porciones": d["porciones_usadas"],
                        "unidades": d["unidades"],
                        "unidad_compra": d["ingredientes"]["unidad_compra"],
                    }
                    for d in cargar_ingredientes_orden(p["id"])
                ],
                f"orden_{p['id']}",
            )
