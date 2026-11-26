"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : app.py  (punto de entrada:  streamlit run app.py)
Librerías : streamlit, supabase, pandas
Propósito : Sistema de inventario de alimentos y gestión de mermas.
            Muestra el login y, según el rol, la vista de cocina o la de
            administrador.
==============================================================================
"""

import streamlit as st

from modulos import vista_admin, vista_cocina
from modulos.auth import cerrar_sesion, mostrar_login

st.set_page_config(page_title="Gestión de Alimentos", page_icon="🍽️", layout="wide")

perfil = st.session_state.get("perfil")

if perfil is None:
    mostrar_login()
    st.stop()  # sin sesión no se ejecuta nada más

# Barra lateral con el usuario y el botón de salida
with st.sidebar:
    st.write(f"👤 **{perfil['usuario']}** · {perfil['rol']}")
    if st.button("Cerrar sesión"):
        cerrar_sesion()

# ------------------------------------------------------------------------------
# NAVEGACIÓN SEGÚN EL ROL
# cocina        -> solo la vista operativa
# administrador -> acceso total: panel gerencial y también la vista de cocina
# ------------------------------------------------------------------------------
if perfil["rol"] == "cocina":
    vista_cocina.mostrar(perfil)
elif perfil["rol"] == "administrador":
    vista = st.sidebar.radio("Vista", ["Panel gerencial", "Cocina"])
    if vista == "Panel gerencial":
        vista_admin.mostrar()
    else:
        vista_cocina.mostrar(perfil)
