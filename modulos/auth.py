"""
==============================================================================
EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA · I CRIM SISTEMAS DE ARMAS
Alumno    : Bastián Gonzalo Castro Montoya
Profesor  : Dr. Carlos Santibáñez Rodríguez
Fecha     : 26-11-2026
Archivo   : modulos/auth.py
Librerías : hashlib, hmac (estándar), streamlit
Propósito : Inicio de sesión por rol (cocina / administrador).
==============================================================================
"""

import hashlib
import hmac

import streamlit as st

from modulos.algoritmos import busqueda_secuencial
from modulos.basedatos import cargar_usuarios


def cifrar(clave: str) -> str:
    """SHA-256: mismo cálculo que encode(sha256(...)) en Supabase."""
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def validar_usuario(usuario: str, clave: str):
    """Devuelve {'usuario', 'rol'} si las credenciales son correctas; si no, None."""
    # BÚSQUEDA SECUENCIAL del usuario dentro de la lista traída de la base
    encontrado = busqueda_secuencial(
        cargar_usuarios(), lambda u: u["usuario"], usuario.strip().lower()
    )
    # Se compara el hash, nunca la clave en texto plano.
    # hmac.compare_digest compara en tiempo constante (evita ataques por tiempo).
    if encontrado and hmac.compare_digest(
        encontrado["clave_hash"].strip(), cifrar(clave)
    ):
        return {"usuario": encontrado["usuario"], "rol": encontrado["rol"]}
    return None


def mostrar_login():
    """Formulario de ingreso. Si es válido, guarda el perfil en st.session_state."""
    st.title("🍽️ Gestión de Alimentos y Mermas")
    with st.form("login"):
        usuario = st.text_input("Usuario")
        clave = st.text_input("Clave", type="password")
        ingresar = st.form_submit_button("Ingresar")
    if ingresar:
        perfil = validar_usuario(usuario, clave)
        if perfil:
            # st.session_state mantiene la sesión entre recargas de la página
            st.session_state["perfil"] = perfil
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos.")


def cerrar_sesion():
    st.session_state.clear()
    st.rerun()
