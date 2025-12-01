<div align="center">
  <img src="https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/banner.svg" alt="VisiLens Logo" width="100%" />
  
  # VisiLens

  **El Excel para desarrolladores**

  > **Abre millones de filas en segundos. Local, rápido y ligero.**
  
  VisiLens es una interfaz web de alto rendimiento, pensada para la exploración de conjuntos de datos en local. Aprovecha la potencia de [VisiData](https://www.visidata.org/) para visualizar y filtrar al instante archivos CSV, Parquet, Excel y JSON.

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![VisiData Engine](https://img.shields.io/badge/Engine-VisiData-orange.svg)](https://www.visidata.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org/)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
  [![PyPI](https://img.shields.io/pypi/v/vdweb.svg)](https://pypi.org/project/vdweb/0.1.1/)

  [English](../README.md) • [简体中文](README_zh.md) • [Español](README_es.md) • [日本語](README_ja.md) • [Русский](README_ru.md)

  [Características](#características) • [Instalación](#instalación) • [Uso](#uso) • [Arquitectura](#arquitectura) • [Contribución](#contribución)
</div>

<div align="center">
  <img src="https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/demo.gif" alt="VisiLens Demo" width="100%" />
</div>


---

## 🚀 ¿Por qué VisiLens?

Explorar datos no debería implicar escribir siempre el mismo código en Pandas ni esperar a que arranque un software de hoja de cálculo pesado como Excel. **VisiLens** es un **visor de CSV** y **explorador de Parquet** moderno que combina la velocidad extrema de **VisiData** con una interfaz web ligera.

- **⚡️ Carga 1 millón de filas en menos de 2 segundos:** gracias al motor de VisiData, altamente optimizado.
- **🔒 Todo en local:** tus datos nunca salen de tu máquina. Nada se sube a la nube.
- **🛠 Cero configuración:** flujo de trabajo orientado a la CLI: canaliza los datos, explóralos y sigue programando.
- **🔌 Soporte amplio de formatos:** abre CSV, TSV, JSON, Parquet, Excel, SQLite y [más de 50 formatos](https://www.visidata.org/formats/).

## ✨ Características

- **Visualización instantánea de datos:** basta con ejecutar `visilens data.csv` para visualizar al instante conjuntos de datos grandes.
- **Ordenación y filtrado desde el backend:** ejecuta consultas complejas sobre millones de filas apoyándote en el motor de VisiData.
- **Cuadrícula de datos virtualizada y ligera:** vista de tabla basada en React, diseñada para un desplazamiento fluido incluso con muchas filas.
- **Cero configuración:** no necesitas montar una base de datos; funciona como visor independiente de CSV/Parquet.

### 📂 Formatos Soportados
VisiLens aprovecha los cargadores de VisiData para soportar una amplia gama de formatos desde el primer momento:
- **Tabular:** `.csv`, `.tsv`, `.xlsx` (Excel), `.parquet`
- **Estructurado:** `.json`, `.jsonl`, `.yaml`
- **Base de datos:** `.sqlite`, `.db`
- **Código:** `.pcap` (Wireshark), `.xml`, `.html` tablas

## 📊 Pruebas de rendimiento

Nos tomamos el rendimiento muy en serio. Así se comporta VisiLens al abrir un conjunto de datos CSV de **1.000.000 de filas** en un MacBook Air estándar (M2):

| Herramienta | Tiempo de Carga (1M Filas) | Huella de Memoria | Ordenación Interactiva |
| :--- | :--- | :--- | :--- |
| **VisiLens** | **~1.7s** | **Mínima (< 50MB Total)** | **Instantánea** (Backend: < 0.4s) |
| Excel | > 30s (A menudo falla) | Alta (Bloquea RAM) | Lenta/Sin respuesta |
| **GUI basada en Pandas** | > 15s (Arranque en frío) | Alta (Todo el DF en RAM) | Lenta (No virtualizada) |
| Jupyter (print df) | Rápida | Media | Texto estático |

*Datos de prueba: 1M filas, 3 columnas (tipos mixtos). Las cifras proceden de mi MacBook Air M2 en un uso real de desarrollo.*

## 📦 Instalación

VisiLens está disponible como un paquete de Python.

```bash
pip install visilens
```

*Nota: VisiLens requiere Python 3.10 o superior.*

## 💻 Uso

### Interfaz de Línea de Comandos

La forma principal de usar VisiLens es a través de la línea de comandos.

```bash
# Abrir un archivo CSV
visilens data.csv

# Abrir un archivo Parquet
visilens large-dataset.parquet

# Abrir un archivo Excel
visilens spreadsheet.xlsx

# Lanzar sin abrir el navegador automáticamente
visilens data.json --no-browser

# Especificar un puerto personalizado
visilens data.csv --port 9000
```

### Interfaz Web

Una vez lanzado, VisiLens se abre en su navegador predeterminado (generalmente `http://localhost:8000`).

1.  **Ver Datos:** Desplácese por su conjunto de datos de manera eficiente.
2.  **Ordenar:** Haga clic en los encabezados de las columnas para ordenar ascendente/descendente.
3.  **Filtrar:** Use las entradas de filtro para buscar dentro de las columnas.
4.  **Cargar Nuevos Datos:** (Próximamente) Arrastre y suelte archivos directamente en la ventana.

## 🏗 Arquitectura

VisiLens está construido sobre una pila moderna y robusta diseñada para el rendimiento:

*   **Backend:** Servidor FastAPI que une VisiData y el navegador.
*   **Comunicación:** WebSockets transmiten fragmentos bajo demanda.
*   **Frontend:** Cuadrícula React que renderiza solo lo que ve.

![Diagrama de Arquitectura](https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/diagram.png)

## 🗺 Hoja de Ruta

Estamos trabajando activamente para hacer de VisiLens el compañero de datos local definitivo.

- [x] **v0.1:** Motor Principal, Desplazamiento Virtual, Ordenación, Filtrado.
- [ ] **Integración con Jupyter:** Lanzar VisiLens directamente desde una celda de notebook (`visilens.view(df)`).
- [ ] **Carga de archivos arrastrar y soltar**
- [ ] **Gráficos:** Histogramas rápidos y gráficos de dispersión a través de Vega-Lite.
- [ ] **Edición:** Editar celdas y guardar cambios en CSV/Parquet.
- [ ] **Soporte SQL:** Conectar directamente a SQLite/Postgres/DuckDB.

## 🛠 Desarrollo

¿Quieres contribuir? ¡Genial! Aquí se explica cómo configurar el entorno de desarrollo.

### Requisitos Previos

- Python 3.10+
- Node.js 18+
- npm o pnpm

### Configuración

1.  **Clonar el repositorio**
    ```bash
    git clone https://github.com/PStarH/VisiLens.git
    cd VisiLens
    ```

2.  **Configuración del Backend**
    ```bash
    # Crear entorno virtual
    python -m venv .venv
    source .venv/bin/activate  # o .venv\Scripts\activate en Windows

    # Instalar dependencias
    pip install -e ".[dev]"
    ```

3.  **Configuración del Frontend**
    ```bash
    cd frontend
    npm install
    ```

4.  **Ejecutar Localmente**

  Terminal 1 (Backend):
  ```bash
  uvicorn backend.main:app --reload --port 8000
  ```

  Terminal 2 (Frontend):
  ```bash
  cd frontend
  npm run dev
  ```

5.  **Construir activos del frontend (opcional)**

  Si prefiere ejecutar solo la CLI de Python (sin un servidor de desarrollo Vite separado), puede construir el frontend una vez:

  ```bash
  cd frontend
  npm run build
  ```

  Esto produce un paquete de producción bajo `frontend/dist/` que se copia en `vdweb/static/` para lanzamientos. Los usuarios finales solo ejecutan:

  ```bash
  visilens path/to/data.csv
  ```

## 🤝 Contribución

### Para Colaboradores: dónde viven las cosas

- **Paquete Python (`vdweb/`):** Este es el paquete instalable publicado en PyPI. Los puntos de entrada CLI `visilens` / `visilens` se resuelven en `visilens.cli:main` como se configura en `pyproject.toml`.
- **Backend de desarrollo (`backend/`):** Una aplicación FastAPI separada utilizada solo para desarrollo local (`uvicorn backend.main:app`). Refleja el comportamiento del backend empaquetado pero no es lo que los usuarios importan cuando instalan `visilens`.
- **Lógica central:** La capa de acceso a datos impulsada por VisiData vive en `vdweb/core.py` (y se refleja en `backend/core.py` para la aplicación de desarrollo). Si desea cambiar cómo se cargan/ordenan/filtran los datos, comience aquí.

### Flujo de trabajo típico del colaborador

1. Edite la lógica del backend / núcleo en `vdweb/` (y actualice `backend/` si es necesario para la paridad de desarrollo).
2. Ejecute el backend de desarrollo + frontend localmente como se describe en [Desarrollo](#-desarrollo).
3. Si cambia la aplicación React y desea que esos cambios se envíen, ejecute `npm run build` en `frontend/` para que el paquete que se copiará en `vdweb/static/` esté actualizado.

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](../LICENSE) para más detalles.

---

<div align="center">
  Hecho con ❤️ por <a href="https://github.com/PStarH">PStarH</a> y la Comunidad de Código Abierto.
</div>

---
*Este README fue traducido por IA y no ha sido revisado. Siéntase libre de enviar un PR para mejorarlo.*
