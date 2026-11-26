# 🍽️ Sistema de Inventario de Alimentos y Gestión de Mermas

**Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas**
**Alumno:** Bastián Gonzalo Castro Montoya · **Profesor:** Dr. Carlos Santibáñez Rodríguez · **Fecha:** 26-11-2026

Aplicación en **Streamlit + Supabase** que, a partir de un menú y la cantidad de comensales, calcula los ingredientes a utilizar, las unidades a comprar (productos indivisibles), la merma, la pérdida por merma, el costo por plato y el precio de venta con 25 % de ganancia.

## Perfiles
| Perfil | Acceso |
|---|---|
| `cocina` | Genera órdenes y ve solo la preparación: porciones a usar y unidades a retirar de bodega. No ve costos ni mermas. Gestiona la cola de órdenes pendientes (FIFO, o fuera de turno si una orden se termina antes). |
| `administrador` | Acceso total: KPIs, historial filtrable y ordenable, análisis de mermas, consulta de insumos y vista de cocina. Las métricas consideran solo órdenes **preparadas**. |

## Reglas de cálculo
```
porciones_usadas = ceil(porciones_receta × comensales / 4)
unidades         = ceil(porciones_usadas / porciones_unidad)
merma            = unidades × porciones_unidad − porciones_usadas
pérdida          = merma / porciones_unidad × costo
costo por plato  = costo total / comensales
precio de venta  = costo por plato × 1,25
```

## Algoritmos y estructuras de datos
| Contenido | Uso en la aplicación |
|---|---|
| Clases y TDA lista | `Ingrediente`, `Receta`, `Orden`; ingredientes de cada receta |
| TDA cola (FIFO) | Órdenes pendientes de cocina, en orden de llegada |
| TDA cola con prioridad | Ranking de menús con mayor pérdida por merma |
| Ordenamiento interno (Quicksort) | Tabla de ingredientes, rankings e historial con 10 órdenes o menos |
| Ordenamiento externo (mezcla por bloques en disco) | Historial con más de 10 órdenes (elección automática) |
| Búsqueda secuencial | Validación de usuario en el login, consulta de insumos y orden fuera de turno |

## Estructura
```
app.py                    # entrada: login y navegación por rol
database/esquema.sql      # tablas, datos (10 ingredientes, 10 recetas) y permisos
modulos/
├── modelos.py            # clases (Ingrediente, Receta, Orden) y TDA Cola
├── calculos.py           # motor de cálculo de insumos, merma y costos
├── algoritmos.py         # Quicksort (interno), mezcla por bloques (externo),
│                         # búsqueda secuencial y TDA cola con prioridad
├── basedatos.py          # consultas a Supabase
├── auth.py               # login con búsqueda secuencial y claves SHA-256
├── vista_cocina.py       # interfaz del perfil cocina
└── vista_admin.py        # panel gerencial del administrador
```

## Ejecución
1. `python -m venv venv` y `.\venv\Scripts\Activate.ps1`
2. `pip install -r requirements.txt`
3. Ejecutar `database/esquema.sql` en el SQL Editor de Supabase y crear los usuarios con su clave cifrada (`encode(sha256('clave'::bytea), 'hex')`).
4. Crear `.streamlit/secrets.toml`:
   ```toml
   [supabase]
   url = "https://xxxxx.supabase.co"
   key = "sb_secret_..."
   ```
5. `streamlit run app.py`

La cantidad de comensales solo acepta números enteros mayores que cero.

Las credenciales no están en el repositorio: `secrets.toml` está excluido en `.gitignore` y las claves de usuario se guardan cifradas (SHA-256).