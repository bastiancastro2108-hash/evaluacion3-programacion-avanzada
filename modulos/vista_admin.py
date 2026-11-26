"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : modulos/vista_admin.py
Librerías : streamlit, pandas
Propósito : Panel gerencial del perfil ADMINISTRADOR (acceso total):
            KPIs, historial filtrable, análisis de mermas y consulta de insumos.
==============================================================================
"""

import pandas as pd
import streamlit as st

from modulos.algoritmos import (
    ColaPrioridad,
    busqueda_secuencial,
    ordenamiento_externo,
    quicksort,
)
from modulos.basedatos import (
    cargar_detalles,
    cargar_ingredientes,
    cargar_ordenes,
    cargar_pendientes,
)

ZONA_HORARIA = "America/Santiago"

# Sobre este número de registros el historial se ordena con el algoritmo
# EXTERNO (mezcla por bloques en disco); con menos, con el INTERNO (Quicksort).
# Así se simula la decisión real: los volúmenes grandes no se cargan completos
# en memoria.
UMBRAL_EXTERNO = 10


def _pesos(valor: float) -> str:
    """Formato chileno: 12345.6 -> $12.346"""
    return "$" + f"{valor:,.0f}".replace(",", ".")


def mostrar():
    st.header("📊 Panel gerencial")
    st.caption("Métricas calculadas solo con órdenes PREPARADAS.")
    if st.button("🔄 Actualizar datos"):
        st.rerun()

    # Solo las órdenes PREPARADAS entran en las métricas; las pendientes se informan aparte
    ordenes = cargar_ordenes()
    detalles = cargar_detalles()
    pendientes = len(cargar_pendientes())
    st.caption(
        f"⏳ Órdenes pendientes en cocina (no incluidas en las métricas): **{pendientes}**"
    )
    if not ordenes:
        st.info(
            "Aún no hay órdenes preparadas. Las métricas aparecen cuando cocina marca una orden como preparada."
        )
        _consulta_insumos()
        return

    # ---------------- Preparación de datos ----------------
    # Merma física por orden = suma de las porciones sobrantes de sus ingredientes
    merma_por_orden = {}
    for d in detalles:
        merma_por_orden[d["orden_id"]] = (
            merma_por_orden.get(d["orden_id"], 0) + d["merma"]
        )

    registros = [
        {
            "Orden": o["id"],
            "Fecha": pd.to_datetime(o["fecha"])
            .tz_convert(ZONA_HORARIA)
            .strftime("%d-%m-%Y %H:%M"),
            "Menú": o["recetas"]["nombre"],
            "Comensales": o["comensales"],
            "Costo por plato": float(o["costo_por_plato"]),
            "Costo total": float(o["costo_total"]),
            "Merma física (porciones)": merma_por_orden.get(o["id"], 0),
            "Pérdida por merma": float(o["perdida_merma"]),
            "Valor de venta (plato)": float(o["precio_venta"]),
            # ingreso proyectado = precio por plato × comensales
            "Ingreso proyectado": float(o["precio_venta"]) * o["comensales"],
        }
        for o in ordenes
    ]

    # ---------------- 1. KPIs globales ----------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Servicios realizados", len(registros))
    c2.metric(
        "Costo total de operación", _pesos(sum(r["Costo total"] for r in registros))
    )
    c3.metric(
        "Pérdida total por merma",
        _pesos(sum(r["Pérdida por merma"] for r in registros)),
    )
    c4.metric(
        "Ingresos proyectados", _pesos(sum(r["Ingreso proyectado"] for r in registros))
    )

    tab_historial, tab_mermas, tab_insumos = st.tabs(
        ["📋 Historial de órdenes", "🗑️ Análisis de mermas", "🔎 Consulta de insumos"]
    )

    with tab_historial:
        _historial(registros)
    with tab_mermas:
        _analisis_mermas(registros, detalles)
    with tab_insumos:
        _consulta_insumos()


# ------------------------------------------------------------------------------
# 2. HISTORIAL FILTRABLE Y ORDENABLE
# ------------------------------------------------------------------------------
def _historial(registros: list):
    menus = sorted({r["Menú"] for r in registros})
    filtro = st.multiselect("Filtrar por menú", menus, placeholder="Todos los menús")
    c1, c2 = st.columns(2)
    criterio = c1.selectbox(
        "Ordenar por",
        [
            "Pérdida por merma",
            "Costo total",
            "Comensales",
            "Merma física (porciones)",
            "Orden",
        ],
    )
    descendente = (
        c2.radio("Sentido", ["Mayor a menor", "Menor a mayor"], horizontal=True)
        == "Mayor a menor"
    )

    # Filtro: se conservan solo los menús elegidos (si no se elige ninguno, todos)
    datos = [r for r in registros if not filtro or r["Menú"] in filtro]

    # ELECCIÓN AUTOMÁTICA DEL ALGORITMO según la cantidad de registros a ordenar
    clave = lambda r: r[criterio]
    if len(datos) > UMBRAL_EXTERNO:
        datos = ordenamiento_externo(datos, clave, descendente, tam_bloque=5)
        bloques = -(-len(datos) // 5)  # división hacia arriba
        metodo = f"ordenamiento externo (mezcla de {bloques} bloques de hasta 5 registros en disco)"
    else:
        datos = quicksort(datos, clave, descendente)
        metodo = "ordenamiento interno (Quicksort en memoria)"

    st.dataframe(
        pd.DataFrame(datos),
        hide_index=True,
        width="stretch",
        column_config={
            col: st.column_config.NumberColumn(col, format="$%.0f")
            for col in [
                "Costo por plato",
                "Costo total",
                "Pérdida por merma",
                "Valor de venta (plato)",
                "Ingreso proyectado",
            ]
        },
    )
    st.caption(
        f"{len(datos)} {'orden' if len(datos) == 1 else 'órdenes'} · ordenadas con {metodo}. "
        f"Sobre {UMBRAL_EXTERNO} órdenes se usa el algoritmo externo."
    )


# ------------------------------------------------------------------------------
# 3. ANÁLISIS DE DESECHOS E IMPACTO ECONÓMICO
# ------------------------------------------------------------------------------
def _analisis_mermas(registros: list, detalles: list):
    # Pérdida acumulada por MENÚ
    por_menu = {}
    for r in registros:
        por_menu[r["Menú"]] = por_menu.get(r["Menú"], 0) + r["Pérdida por merma"]

    # Pérdida y merma acumuladas por INGREDIENTE
    por_ingrediente = {}
    for d in detalles:
        nombre = d["ingredientes"]["nombre"]
        actual = por_ingrediente.get(
            nombre, {"Ingrediente": nombre, "Pérdida": 0.0, "Porciones perdidas": 0}
        )
        actual["Pérdida"] += float(d["perdida"])
        actual["Porciones perdidas"] += d["merma"]
        por_ingrediente[nombre] = actual

    # Cola con prioridad: salen primero los menús con MAYOR pérdida
    cola = ColaPrioridad()
    for menu, perdida in por_menu.items():
        cola.encolar(perdida, menu)
    st.subheader("Menús con mayor pérdida por merma")
    for puesto in range(1, min(3, len(por_menu)) + 1):
        perdida, menu = cola.desencolar()
        st.write(f"**{puesto}.** {menu} — {_pesos(perdida)}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Pérdida por menú ($)**")
        tabla_menu = quicksort(
            [{"Menú": m, "Pérdida": p} for m, p in por_menu.items()],
            lambda x: x["Pérdida"],
            descendente=True,
        )
        st.bar_chart(pd.DataFrame(tabla_menu), x="Menú", y="Pérdida", horizontal=True)
    with col2:
        st.markdown("**Pérdida por ingrediente ($)**")
        tabla_ing = quicksort(
            list(por_ingrediente.values()), lambda x: x["Pérdida"], descendente=True
        )
        st.bar_chart(
            pd.DataFrame(tabla_ing), x="Ingrediente", y="Pérdida", horizontal=True
        )

    st.markdown("**Detalle por ingrediente**")
    st.dataframe(
        pd.DataFrame(tabla_ing),
        hide_index=True,
        width="stretch",
        column_config={"Pérdida": st.column_config.NumberColumn(format="$%.0f")},
    )


# ------------------------------------------------------------------------------
# 4. CONSULTA DE INSUMOS (búsqueda secuencial)
# ------------------------------------------------------------------------------
def _consulta_insumos():
    ingredientes = cargar_ingredientes()
    nombre = st.text_input("Buscar ingrediente por nombre", placeholder="Ej: Tomate")
    if nombre:
        encontrado = busqueda_secuencial(
            ingredientes, lambda i: i.nombre.lower(), nombre.strip().lower()
        )
        if encontrado:
            st.success(
                f"**{encontrado.nombre}**: {_pesos(encontrado.costo)} por {encontrado.unidad_compra} · "
                f"rinde {encontrado.porciones_unidad} porciones"
            )
        else:
            st.warning("Ingrediente no encontrado.")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Ingrediente": i.nombre,
                    "Costo": i.costo,
                    "Unidad de compra": i.unidad_compra,
                    "Porciones por unidad": i.porciones_unidad,
                }
                for i in ingredientes
            ]
        ),
        hide_index=True,
        width="stretch",
        column_config={"Costo": st.column_config.NumberColumn(format="$%d")},
    )
