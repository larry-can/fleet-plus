<p align="center">
  <img src="src/fleet_plus.png" alt="fleet +" width="200"/>
</p>

<h1 align="center">Gestión integral de flotas.</h1>
<p align="center">
  Una aplicación de escritorio open-source diseñada para gestores de flotas, talleres y empresas de transporte.
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-blue.svg" alt="License"></a>
</p>

<p>fleet+ es una potente aplicación de escritorio que centraliza todas las herramientas esenciales para gestionar 
    mantenimientos de vehículos, proveedores y reportes en un solo lugar, con una interfaz moderna y personalizable 
    gracias a customtkinter. Olvídate de múltiples hojas de cálculo y ventanas: aquí tienes todo lo que necesitas.
</p>
<h2>Apoya fleet+</h2>
<p>
Si encuentras fleet+ útil y quieres apoyar su desarrollo, ¡considera hacer una contribución! Tu apoyo ayuda a mantener 
el proyecto activo y en constante mejora. Próximamente, se implementarán nuevas funcionalidades y mejoras basadas en los 
comentarios de la comunidad. Como líneas de desarrollo futuras, se planea integrar notificaciones automáticas para mantenimientos, 
llamado Calendario General de Vehículos (CGV) y una app móvil complementaria para gestionar la flota desde cualquier lugar. Además, 
estamos investigando para implementar la automatización de recogida de datos por medio de sensores.
</p>

<p align="center">
  <a href="https://www.paypal.me/AlCanoLopez?locale.x=es_ES" target="_blank" class="paypal-link">
    <img src="https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Donate via PayPal">
  </a>
  <a href="https://www.buymeacoffee.com/albcano83a">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Buy-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee">
  </a>

  ![captura](/src/interfaz.png)
</p>

---

## Características principales

- Registro y gestión de mantenimientos de vehículos.  
- Gestión de proveedores, componentes y productos.  
- Búsqueda, filtrado y actualización de registros.  
- Generación de reportes en PDF mediante **reportlab**.  
- Interfaz moderna y personalizable con **customtkinter**.  
- Base de datos **SQLite autogenerada** si no existe.

---

## 🧰 Tecnologías y dependencias

- **Python 3.10+**  
- **customtkinter** — interfaz gráfica moderna  
- **sqlite3** — almacenamiento ligero integrado  
- **reportlab** — generación de PDFs  

### Instalación de dependencias

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
# .\venv\Scripts\activate  # Windows

pip install -r requirements.txt




# fleet +

**fleet +** es una aplicación de escritorio desarrollada en Python para gestionar el mantenimiento de flotas y generar reportes en PDF. Utiliza **customtkinter** para la interfaz gráfica y **sqlite3** como base de datos.

---

## Características principales

- Registro y gestión de mantenimientos de vehículos.  
- Gestión de proveedores, componentes y productos.  
- Búsqueda, filtrado y actualización de registros.  
- Generación de reportes en PDF mediante **reportlab**.  
- Interfaz moderna y personalizable con **customtkinter**.  
- Base de datos **SQLite autogenerada** si no existe.

---

## Tecnologías y dependencias

- **Python 3.10+**
- `customtkinter` — interfaz gráfica moderna.  
- `sqlite3` — almacenamiento ligero integrado.  
- `reportlab` — generación de PDFs.  

### Instalación de dependencias

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
# .\venv\Scripts\activate  # Windows

pip install -r requirements.txt
