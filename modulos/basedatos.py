"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : modulos/basedatos.py
Librerías : streamlit, supabase
Propósito : Todas las consultas a Supabase. Ningún otro archivo habla con la
            base de datos (separación entre datos, cálculo e interfaz).
==============================================================================
"""

from datetime import datetime, timezone

import streamlit as st
from supabase import create_client

from modulos.modelos import Ingrediente, ItemReceta, Orden, Receta


# ------------------------------------------------------------------------------
# CONEXIÓN
# La URL y la key se leen de .streamlit/secrets.toml (st.secrets), nunca se
# escriben en el código. @st.cache_resource crea el cliente UNA sola vez y lo
# reutiliza en cada recarga de la página.
# ------------------------------------------------------------------------------
@st.cache_resource
def get_cliente():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])


# ------------------------------------------------------------------------------
# LECTURA DE CATÁLOGOS
# @st.cache_data guarda el resultado 10 minutos: el catálogo casi no cambia
# y así no se consulta la base en cada clic.
# ------------------------------------------------------------------------------
def _crear_ingrediente(fila: dict) -> Ingrediente:
    return Ingrediente(
        fila["id"],
        fila["nombre"],
        int(fila["costo"]),
        fila["unidad_compra"],
        int(fila["porciones_unidad"]),
    )


@st.cache_data(ttl=600)
def cargar_ingredientes() -> list:
    filas = get_cliente().table("ingredientes").select("*").order("id").execute().data
    return [_crear_ingrediente(f) for f in filas]


@st.cache_data(ttl=600)
def cargar_recetas() -> list:
    """Una sola consulta trae cada receta con sus ingredientes (equivale a dos JOIN)."""
    filas = (
        get_cliente()
        .table("recetas")
        .select(
            "id, nombre, base_comensales, receta_ingredientes(id, porciones, ingredientes(*))"
        )
        .order("id")
        .execute()
        .data
    )
    recetas = []
    for f in filas:
        # Se respeta el orden en que se escribió la receta (id de receta_ingredientes)
        items = sorted(f["receta_ingredientes"], key=lambda x: x["id"])
        recetas.append(
            Receta(
                f["id"],
                f["nombre"],
                f["base_comensales"],
                [
                    ItemReceta(
                        _crear_ingrediente(i["ingredientes"]), int(i["porciones"])
                    )
                    for i in items
                ],
            )
        )
    return recetas


def cargar_usuarios() -> list:
    """Lista de usuarios (con su clave cifrada) para validar el login."""
    return (
        get_cliente()
        .table("usuarios")
        .select("usuario, clave_hash, rol")
        .execute()
        .data
    )


# ------------------------------------------------------------------------------
# ÓRDENES: GUARDAR Y CONSULTAR
# ------------------------------------------------------------------------------
def guardar_orden(orden: Orden, usuario: str) -> int:
    """Guarda la orden y su detalle. Devuelve el id de la orden creada."""
    cliente = get_cliente()
    nueva = (
        cliente.table("ordenes")
        .insert(
            {
                "receta_id": orden.receta.id,
                "comensales": orden.comensales,
                "costo_total": orden.costo_total,
                "costo_por_plato": orden.costo_por_plato,
                "precio_venta": orden.precio_venta,
                "perdida_merma": orden.perdida_merma,
                "usuario": usuario,
            }
        )
        .execute()
        .data[0]
    )

    cliente.table("orden_detalle").insert(
        [
            {
                "orden_id": nueva["id"],
                "ingrediente_id": d.ingrediente.id,
                "porciones_usadas": d.porciones_usadas,
                "unidades": d.unidades,
                "merma": d.merma,
                "costo": d.costo,
                "perdida": d.perdida,
            }
            for d in orden.detalle
        ]
    ).execute()
    return nueva["id"]


def cargar_pendientes() -> list:
    """Órdenes aún no preparadas, de la más antigua a la más nueva (FIFO: el id crece con cada orden)."""
    return (
        get_cliente()
        .table("ordenes")
        .select("id, comensales, fecha, recetas(nombre)")
        .eq("estado", "pendiente")
        .order("id")
        .execute()
        .data
    )


def cargar_ingredientes_orden(id_orden: int) -> list:
    """Ingredientes de UNA orden, solo con datos operativos (sin costos ni merma)."""
    return (
        get_cliente()
        .table("orden_detalle")
        .select("porciones_usadas, unidades, ingredientes(nombre, unidad_compra)")
        .eq("orden_id", id_orden)
        .order("id")
        .execute()
        .data
    )


def marcar_preparada(id_orden: int) -> None:
    """Cambia el estado en la base de datos: así no se pierde al cerrar sesión."""
    get_cliente().table("ordenes").update(
        {
            "estado": "preparada",
            "fecha_preparacion": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", id_orden).execute()


def cargar_ordenes() -> list:
    """Historial de órdenes PREPARADAS (las que cuentan en las métricas)."""
    return (
        get_cliente()
        .table("ordenes")
        .select("*, recetas(nombre)")
        .eq("estado", "preparada")
        .order("fecha", desc=True)
        .execute()
        .data
    )


def cargar_detalles() -> list:
    """Detalle por ingrediente de las órdenes PREPARADAS (para analizar mermas).
    ordenes!inner obliga a que exista la orden y permite filtrar por su estado."""
    return (
        get_cliente()
        .table("orden_detalle")
        .select(
            "*, ingredientes(nombre, unidad_compra), ordenes!inner(estado, recetas(nombre))"
        )
        .eq("ordenes.estado", "preparada")
        .execute()
        .data
    )
