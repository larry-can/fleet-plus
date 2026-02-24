import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Ruta base del proyecto y BD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app_mantenimiento.db")

def inicializar_base_datos():
    """Crea la base de datos y todas las tablas necesarias si no existen."""
    db_existe = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not db_existe:
        print("Creando base de datos...")

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS TipoComponente (
            id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT
        );

        CREATE TABLE IF NOT EXISTS Producto (
            id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tipo INTEGER NOT NULL,
            marca TEXT,
            modelo TEXT,
            tipo TEXT,
            descripcion TEXT,
            vida_util_km INTEGER,
            vida_util_meses INTEGER,
            FOREIGN KEY (id_tipo) REFERENCES TipoComponente(id_tipo)
        );

        CREATE TABLE IF NOT EXISTS Coche (
            matricula TEXT PRIMARY KEY,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            km_actuales INTEGER,
            fecha_matriculacion DATE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Mantenimiento (
            id_mantenimiento INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            id_producto INTEGER NOT NULL,
            fecha DATE NOT NULL,
            km INTEGER NOT NULL,
            descripcion TEXT,
            FOREIGN KEY (matricula) REFERENCES Coche(matricula),
            FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
        );

        CREATE TABLE IF NOT EXISTS Obligaciones (
            id_obligacion INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            fecha_inicio DATE,
            fecha_vencimiento DATE,
            estado TEXT DEFAULT 'Vigente',
            FOREIGN KEY (matricula) REFERENCES Coche(matricula)
        );

        CREATE TABLE IF NOT EXISTS Proveedor (
            id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cif_nif TEXT UNIQUE,
            tipo TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            descripcion TEXT
        );

        CREATE TABLE IF NOT EXISTS Factura (
            id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
            id_proveedor INTEGER NOT NULL,
            num_factura TEXT NOT NULL,
            fecha_emision DATE,
            importe_total REAL,
            matricula TEXT,
            FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor),
            FOREIGN KEY (matricula) REFERENCES Coche(matricula),
            UNIQUE (id_proveedor, num_factura)
        );

        CREATE TABLE IF NOT EXISTS Gasto (
            id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            id_factura INTEGER,
            fecha DATE NOT NULL,
            categoria TEXT,
            concepto TEXT NOT NULL,
            importe REAL NOT NULL,
            observaciones TEXT,
            FOREIGN KEY (matricula) REFERENCES Coche(matricula),
            FOREIGN KEY (id_factura) REFERENCES Factura(id_factura)
        );
    """)

    conn.commit()
    conn.close()

    if not db_existe:
        print("Base de datos creada correctamente.")
    else:
        print("Base de datos existente, arrancamos.")


class MantenimientoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fleet Plus - Gestión Integral de Flotas")
        self.root.geometry("1920x1080")

        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

        # --- Crear tabs principales ---
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Pestañas principales
        self.tab_coches = self.tabview.add("Vehículos")
        self.tab_agregar_coche = self.tabview.add("➕ Gestión")
        self.tab_agregar_componente = self.tabview.add("➕ Componentes")
        self.tab_agregar_producto = self.tabview.add("➕ Productos")
        self.tab_agregar_mantenimiento = self.tabview.add("➕ Mantenimientos")
        self.tab_obligaciones = self.tabview.add("➕ Obligaciones")
        self.tab_proveedores = self.tabview.add("➕ Proveedores")
        self.tab_facturas = self.tabview.add("➕ Facturas")
        self.tab_gastos = self.tabview.add("➕ Gastos")

        # Inicializar cada pestaña
        self.crear_tab_coches()
        self.crear_tab_agregar_coche()
        self.crear_tab_agregar_componente()
        self.crear_tab_agregar_producto()
        self.crear_tab_agregar_mantenimiento()
        self.crear_tab_obligaciones()
        self.crear_tab_proveedores()
        self.crear_tab_facturas()
        self.crear_tab_gastos()

    def obtener_matriculas(self, mostrar_detalle=False):
        """Devuelve una lista de matrículas o 'matrícula (marca modelo)' si mostrar_detalle=True."""
        try:
            if mostrar_detalle:
                cursor = self.conn.execute("SELECT matricula, marca, modelo FROM Coche ORDER BY matricula")
                return [f"{row['matricula']} ({row['marca']} {row['modelo']})" for row in cursor.fetchall()]
            else:
                cursor = self.conn.execute("SELECT matricula FROM Coche ORDER BY matricula")
                return [row["matricula"] for row in cursor.fetchall()]
        except Exception as e:
            print("Error al obtener matrículas:", e)
            return []

    
    def actualizar_combo_matriculas(self):
        """Actualiza el combo de matrículas en la pestaña Obligaciones."""
        if hasattr(self, "obl_coche_cb"):
            self.obl_coche_cb.configure(values=self.obtener_matriculas())

    def actualizar_km(self):
        """Actualiza los kilómetros del coche seleccionado."""
        matricula = self.coche_var.get().split("(")[0].strip()
        nuevo_km = self.km_var.get().strip()

        if not matricula:
            messagebox.showwarning("Atención", "Selecciona un vehículo antes de actualizar los kilómetros.")
            return

        if not nuevo_km.isdigit():
            messagebox.showerror("Error", "Introduce un número válido para los kilómetros.")
            return

        try:
            self.conn.execute("UPDATE Coche SET km_actuales = ? WHERE matricula = ?", (nuevo_km, matricula))
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Kilometraje actualizado a {nuevo_km} km para {matricula}.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el kilometraje: {e}")

    def actualizar_combo_producto(self, event=None):
        """Actualiza el combo de productos según el tipo de componente seleccionado."""
        tipo_seleccionado = self.mant_tipo_var.get().strip()
        if not tipo_seleccionado:
            self.combo_mant_producto["values"] = []
            return
        try:
            query = """
                SELECT p.id_producto, p.marca, p.modelo, p.tipo
                FROM Producto p
                JOIN TipoComponente tc ON p.id_tipo = tc.id_tipo
                WHERE tc.nombre = ?
                ORDER BY p.marca, p.modelo
            """
            productos = self.conn.execute(query, (tipo_seleccionado,)).fetchall()

            lista = [f"{r['marca']} {r['modelo']} ({r['tipo']})" if r['tipo'] else f"{r['marca']} {r['modelo']}" for r in productos]
            self.combo_mant_producto["values"] = lista

            # Si hay productos, selecciona el primero por defecto
            if lista:
                self.combo_mant_producto.set(lista[0])

        except Exception as e:
            print("Error al actualizar combo de productos:", e)
            self.combo_mant_producto["values"] = []


    # PESTAÑA VEHÍCULOS

    def crear_tab_coches(self):
        # --- FRAME PRINCIPAL CON SCROLL ---
        canvas = ctk.CTkCanvas(self.tab_coches, bg="#242424", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.tab_coches, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        # --- Frame interno donde van los contenidos ---
        frame_contenedor = ctk.CTkFrame(canvas)
        frame_contenedor.grid_columnconfigure(0, weight=1)

        # Vincular el frame al canvas
        canvas_window = canvas.create_window((0, 0), window=frame_contenedor, anchor="n")

        # Actualizar el scrollregion automáticamente
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
        # Centra el frame_contenedor horizontalmente
            canvas.itemconfig(canvas_window, width=event.width)

        frame_contenedor.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)


        # --- Permitir scroll con la rueda del ratón desde cualquier parte ---

        def _on_mousewheel(event):
            """Scroll para Windows y macOS."""
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_linux_scroll(event):
            """Scroll para Linux (botón 4 y 5)."""
            if event.num == 4:
                canvas.yview_scroll(-3, "units")
            elif event.num == 5:
                canvas.yview_scroll(3, "units")

        def _bound_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)     # Windows / macOS
            canvas.bind_all("<Button-4>", _on_linux_scroll)     # Linux scroll up
            canvas.bind_all("<Button-5>", _on_linux_scroll)     # Linux scroll down

        def _unbound_to_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        # Asociar cuando el ratón entra o sale del canvas
        frame_contenedor.bind("<Enter>", _bound_to_mousewheel)
        frame_contenedor.bind("<Leave>", _unbound_to_mousewheel)    

        # --- Frame de selección del vehículo ---
        frame_coche = ctk.CTkFrame(frame_contenedor)
        frame_coche.grid(row=0, column=0, pady=15, sticky="n")
        frame_coche.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_coche, text="Selecciona el vehículo:", font=("Arial", 18)).grid(row=0, column=0, padx=10, sticky="e")
        self.coche_var = ctk.StringVar()
        self.combo_coche = ttk.Combobox(frame_coche, textvariable=self.coche_var, state="readonly", width=40)
        self.combo_coche.grid(row=0, column=1, padx=5)
        self.combo_coche.bind("<<ComboboxSelected>>", lambda e: [
        self.mostrar_mantenimientos(),
        self.mostrar_gastos_coche(),
        self.mostrar_facturas_coche()
        ])

        # Botón para exportar PDF
        ctk.CTkButton(frame_coche, text="Exportar a PDF", command=self.exportar_pdf).grid(row=1, column=0, columnspan=2, pady=10)

        # --- Frame de información del coche ---
        frame_info = ctk.CTkFrame(frame_contenedor)
        frame_info.grid(row=1, column=0, pady=10, sticky="n")
        ctk.CTkLabel(frame_info, text="Fecha de matriculación:", font=("Arial", 18)).pack(side="left", padx=10)
        self.fecha_mat_var = ctk.StringVar()
        self.label_fecha_mat = ctk.CTkLabel(frame_info, textvariable=self.fecha_mat_var, font=("Arial", 18, "bold"))
        self.label_fecha_mat.pack(side="left", padx=5)

        # --- Frame de kilómetros ---
        frame_km = ctk.CTkFrame(frame_contenedor)
        frame_km.grid(row=2, column=0, pady=10, sticky="n")
        ctk.CTkLabel(frame_km, text="Kilómetros actuales:", font=("Arial", 18)).pack(side="left", padx=10)
        self.km_var = ctk.StringVar()
        self.entry_km = ctk.CTkEntry(frame_km, textvariable=self.km_var, width=120, font=("Arial", 22))
        self.entry_km.pack(side="left", padx=10)
        ctk.CTkButton(frame_km, text="Actualizar km", command=self.actualizar_km).pack(side="left", padx=10)

        # --- Frame de mantenimientos centrado ---
        self.frame_mantenimientos = ctk.CTkFrame(frame_contenedor)
        self.frame_mantenimientos.grid(row=3, column=0, pady=10, sticky="n")
        self.frame_mantenimientos.grid_columnconfigure(0, weight=1)

        # --- Separador visual ---
        ctk.CTkLabel(frame_contenedor, text="").grid(row=4, column=0, pady=5)

        # --- Frame de obligaciones ---
        self.frame_obligaciones_coche = ctk.CTkFrame(frame_contenedor)
        self.frame_obligaciones_coche.grid(row=5, column=0, pady=10, sticky="n")
        self.frame_obligaciones_coche.grid_columnconfigure(0, weight=1)

        # --- Frame de gastos ---
        self.frame_gastos_coche = ctk.CTkFrame(frame_contenedor)
        self.frame_gastos_coche.grid(row=6, column=0, pady=20, sticky="nsew")
        self.frame_gastos_coche.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.frame_gastos_coche, text="Gastos", font=("Arial", 20, "bold")).pack(pady=10)

        self.tree_gastos_coche = ttk.Treeview(
            self.frame_gastos_coche,
            columns=("fecha", "categoria", "concepto", "importe", "observaciones"),
            show="headings", height=8
        )
        self.tree_gastos_coche.pack(pady=10, fill="x", expand=True)

        for col, title in zip(
            ("fecha", "categoria", "concepto", "importe", "observaciones"),
            ("Fecha", "Categoría", "Concepto", "Importe (€)", "Observaciones")
        ):
            self.tree_gastos_coche.heading(col, text=title)
            self.tree_gastos_coche.column(col, width=150, anchor="center")

        # --- Frame de facturas ---
        self.frame_facturas_coche = ctk.CTkFrame(frame_contenedor)
        self.frame_facturas_coche.grid(row=7, column=0, pady=20, sticky="nsew")
        self.frame_facturas_coche.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.frame_facturas_coche, text="Facturas asociadas al vehículo", font=("Arial", 20, "bold")).pack(pady=10)

        self.tree_facturas_coche = ttk.Treeview(
            self.frame_facturas_coche,
            columns=("num_factura", "proveedor", "fecha_emision", "importe_total"),
            show="headings", height=6
        )
        self.tree_facturas_coche.pack(pady=10, fill="x", expand=True)

        for col, title in zip(
            ("num_factura", "proveedor", "fecha_emision", "importe_total"),
            ("Nº Factura", "Proveedor", "Fecha emisión", "Importe total (€)")
        ):
            self.tree_facturas_coche.heading(col, text=title)
            self.tree_facturas_coche.column(col, width=200, anchor="center")

        # --- Cargar datos y mostrar ---
        self.cargar_coches()
        self.mostrar_mantenimientos()
        self.mostrar_gastos_coche()


    def mostrar_gastos_coche(self, event=None):
        """Muestra los gastos asociados a la matrícula seleccionada en la pestaña Vehículos."""
        if not hasattr(self, "tree_gastos_coche"):
            return

        # Limpiar la tabla
        for fila in self.tree_gastos_coche.get_children():
            self.tree_gastos_coche.delete(fila)

        matricula = self.coche_var.get().split("(")[0].strip()
        if not matricula:
            return

        query = """
            SELECT fecha, categoria, concepto, importe, observaciones
            FROM Gasto
            WHERE matricula = ?
            ORDER BY fecha DESC
        """
        try:
            cursor = self.conn.execute(query, (matricula,))
            gastos = cursor.fetchall()

            total_gastos = 0.0
            for row in gastos:
                importe = float(row["importe"]) if row["importe"] is not None else 0.0
                total_gastos += importe
                self.tree_gastos_coche.insert(
                    "", "end",
                    values=(
                        row["fecha"],
                        row["categoria"],
                        row["concepto"],
                        f"{importe:.2f} €",
                        row["observaciones"]
                    )
                )

            # Mostrar total debajo de la tabla
            if hasattr(self, "label_total_gastos"):
                self.label_total_gastos.destroy()

            self.label_total_gastos = ctk.CTkLabel(
                self.frame_gastos_coche,
                text=f"💰 Total Gastos: {total_gastos:.2f} €",
                font=("Arial", 18, "bold"),
                text_color="lightgreen"
            )
            self.label_total_gastos.pack(pady=(5, 10))

        except Exception as e:
            print("Error al mostrar gastos:", e)

    def mostrar_facturas_coche(self, event=None):
        """Muestra las facturas asociadas al vehículo seleccionado."""
        if not hasattr(self, "tree_facturas_coche"):
            return

        # Limpiar tabla
        for fila in self.tree_facturas_coche.get_children():
            self.tree_facturas_coche.delete(fila)

        matricula = self.coche_var.get().split("(")[0].strip()
        if not matricula:
            return

        query = """
            SELECT 
                f.num_factura,
                p.nombre AS proveedor,
                f.fecha_emision,
                f.importe_total
            FROM Factura f
            JOIN Proveedor p ON f.id_proveedor = p.id_proveedor
            WHERE f.matricula = ?
            ORDER BY f.fecha_emision DESC
        """
        try:
            cursor = self.conn.execute(query, (matricula,))
            facturas = cursor.fetchall()

            total_facturas = 0.0
            for row in facturas:
                importe = float(row["importe_total"]) if row["importe_total"] else 0.0
                total_facturas += importe
                self.tree_facturas_coche.insert(
                    "",
                    "end",
                    values=(
                        row["num_factura"],
                        row["proveedor"],
                        row["fecha_emision"],
                        f"{importe:.2f} €",
                    ),
                )

            # Mostrar total de facturas
            if hasattr(self, "label_total_facturas"):
                self.label_total_facturas.destroy()

            self.label_total_facturas = ctk.CTkLabel(
                self.frame_facturas_coche,
                text=f"📄 Total facturas: {total_facturas:.2f} €",
                font=("Arial", 18, "bold"),
                text_color="lightblue",
            )
            self.label_total_facturas.pack(pady=(5, 10))

        except Exception as e:
            print("Error al mostrar facturas:", e)


    # PESTAÑA GESTIÓN VEHÍCULOS

    def crear_tab_agregar_coche(self):
        frame = ctk.CTkFrame(self.tab_agregar_coche)
        frame.pack(pady=30)

        # === Sección: Registrar nuevo coche ===
        ctk.CTkLabel(frame, text="Registrar nuevo vehículo", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        labels = ["Matrícula:", "Marca:", "Modelo:", "Kilómetros actuales:", "Fecha de matriculación:"]
        self.vars_coche = {}

        for i, label in enumerate(labels):
            ctk.CTkLabel(frame, text=label, font=("Arial", 22)).grid(row=i + 1, column=0, sticky="e", padx=10, pady=8)
            var = ctk.StringVar()
            self.vars_coche[label] = var
            entry = ctk.CTkEntry(frame, textvariable=var, width=220, font=("Arial", 20))
            entry.grid(row=i + 1, column=1, padx=10, pady=8)

        ctk.CTkButton(frame, text="Añadir vehículo", command=self.guardar_coche).grid(row=len(labels) + 1, column=0, columnspan=2, pady=20)

        # === Separador visual ===
        sep_row = len(labels) + 2
        ctk.CTkLabel(frame, text="──────────────────────────────────────────────", font=("Arial", 14)).grid(row=sep_row, column=0, columnspan=2, pady=12)

        # === Sección: Gestión de vehículos existentes ===
        base_row = sep_row + 1
        ctk.CTkLabel(frame, text="Gestión de vehículos existentes", font=("Arial", 18, "bold")).grid(row=base_row, column=0, columnspan=2, pady=8)

        ctk.CTkLabel(frame, text="Selecciona matrícula:", font=("Arial", 22)).grid(row=base_row + 1, column=0, sticky="e", padx=10, pady=6)
        self.combo_gestion = ttk.Combobox(frame, state="readonly", width=40, values=self.obtener_matriculas())
        self.combo_gestion.grid(row=base_row + 1, column=1, pady=6)

        # === Botones de gestión (alineados correctamente) ===
        btn_row = base_row + 2
        ctk.CTkButton(frame, text="Cargar datos", hover_color="#515344",
                    command=self.cargar_datos_coche).grid(row=btn_row, column=0, pady=8, padx=10, sticky="e")

        ctk.CTkButton(frame, text="Refrescar lista", hover_color="#6168B5",
                    command=lambda: self.combo_gestion.configure(values=self.obtener_matriculas())).grid(row=btn_row, column=1, pady=8, padx=10, sticky="w")

        ctk.CTkButton(frame, text="Eliminar vehículo", fg_color="red", hover_color="#990000",
                    command=self.eliminar_coche).grid(row=btn_row + 1, column=0, columnspan=2, pady=8)

        # === Campos de modificación ===
        campos_modif = ["Marca:", "Modelo:", "Kilómetros actuales:", "Fecha de matriculación:"]
        self.vars_modif = {}
        start_row = btn_row + 2

        for i, campo in enumerate(campos_modif):
            ctk.CTkLabel(frame, text=campo, font=("Arial", 22)).grid(row=start_row + i, column=0, sticky="e", padx=10, pady=6)
            var = ctk.StringVar()
            self.vars_modif[campo] = var
            entry = ctk.CTkEntry(frame, textvariable=var, width=220, font=("Arial", 20))
            entry.grid(row=start_row + i, column=1, padx=10, pady=6)

        ctk.CTkButton(frame, text="Guardar cambios", hover_color="#225A04",
                    command=self.guardar_modificaciones_coche).grid(row=start_row + len(campos_modif), column=0, columnspan=2, pady=16)

        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1)

    def guardar_coche(self):
        datos = {k: v.get().strip() for k, v in self.vars_coche.items()}

        if not all([datos["Matrícula:"], datos["Marca:"], datos["Modelo:"], datos["Fecha de matriculación:"]]):
            messagebox.showerror("Error", "Por favor completa todos los campos obligatorios.")
            return

        try:
            km = int(datos["Kilómetros actuales:"]) if datos["Kilómetros actuales:"] else 0
            self.conn.execute(
                "INSERT INTO Coche (matricula, marca, modelo, km_actuales, fecha_matriculacion) VALUES (?, ?, ?, ?, ?)",
                (datos["Matrícula:"], datos["Marca:"], datos["Modelo:"], km, datos["Fecha de matriculación:"])
            )
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Coche {datos['Matrícula:']} añadido correctamente.")

            # Refrescar combos si existen
            for fn in ("cargar_coches", "actualizar_combo_matriculas", "recargar_coches_en_mantenimiento"):
                try:
                    getattr(self, fn)()
                except Exception:
                    pass

            if hasattr(self, "combo_gestion"):
                try:
                    self.combo_gestion.configure(values=self.obtener_matriculas())
                except Exception:
                    pass

            # Limpiar formulario
            for var in self.vars_coche.values():
                var.set("")

            # Refrescar combobox de matrículas en pestaña Facturas
            if hasattr(self, "factura_matricula_cb"):
                try:
                    self.factura_matricula_cb.configure(values=self.obtener_matriculas())
                except Exception:
                    pass

            # Refrescar combobox de matrículas en pestaña Gastos
            if hasattr(self, "gasto_matricula_cb"):
                try:
                    self.gasto_matricula_cb.configure(values=self.obtener_matriculas())
                except Exception:
                    pass    
    

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ya existe un coche con esa matrícula.")
        except ValueError:
            messagebox.showerror("Error", "Introduce un número válido para kilómetros.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el coche: {e}")


    def cargar_datos_coche(self):
        matricula = self.combo_gestion.get()
        if not matricula:
            messagebox.showwarning("Atención", "Selecciona una matrícula primero.")
            return

        try:
            cursor = self.conn.execute("SELECT * FROM Coche WHERE matricula = ?", (matricula,))
            coche = cursor.fetchone()
            if coche:
                self.vars_modif["Marca:"].set(coche["marca"] or "")
                self.vars_modif["Modelo:"].set(coche["modelo"] or "")
                self.vars_modif["Kilómetros actuales:"].set(str(coche["km_actuales"] or ""))
                self.vars_modif["Fecha de matriculación:"].set(coche["fecha_matriculacion"] or "")
            else:
                messagebox.showerror("Error", "No se encontró el coche seleccionado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")


    def guardar_modificaciones_coche(self):
        matricula = self.combo_gestion.get()
        if not matricula:
            messagebox.showwarning("Atención", "Selecciona una matrícula primero.")
            return

        nuevos_datos = {k: v.get().strip() for k, v in self.vars_modif.items()}
        if not all([nuevos_datos["Marca:"], nuevos_datos["Modelo:"], nuevos_datos["Fecha de matriculación:"]]):
            messagebox.showerror("Error", "Completa todos los campos obligatorios antes de guardar.")
            return

        try:
            km = int(nuevos_datos["Kilómetros actuales:"]) if nuevos_datos["Kilómetros actuales:"] else 0
            self.conn.execute(
                """UPDATE Coche
                SET marca = ?, modelo = ?, km_actuales = ?, fecha_matriculacion = ?
                WHERE matricula = ?""",
                (nuevos_datos["Marca:"], nuevos_datos["Modelo:"], km, nuevos_datos["Fecha de matriculación:"], matricula)
            )
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Datos del coche {matricula} actualizados correctamente.")

            # Refrescar combos y limpiar
            try:
                self.cargar_coches()
                self.actualizar_combo_matriculas()
            except Exception:
                pass

            self.combo_gestion.configure(values=self.obtener_matriculas())
            self.combo_gestion.set("")
            for var in self.vars_modif.values():
                var.set("")

        except ValueError:
            messagebox.showerror("Error", "Introduce un número válido para kilómetros.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los cambios: {e}")


    def eliminar_coche(self):
        matricula = self.combo_gestion.get()
        if not matricula:
            messagebox.showwarning("Atención", "Selecciona una matrícula primero.")
            return

        if not messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de eliminar el coche {matricula}? Esta acción no se puede deshacer."):
            return

        try:
            self.conn.execute("DELETE FROM Coche WHERE matricula = ?", (matricula,))
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Coche {matricula} eliminado correctamente.")

            # Refrescar combos y limpiar
            for fn in ("cargar_coches", "actualizar_combo_matriculas", "recargar_coches_en_mantenimiento"):
                try:
                    getattr(self, fn)()
                except Exception:
                    pass

            self.combo_gestion.configure(values=self.obtener_matriculas())
            self.combo_gestion.set("")
            for var in self.vars_modif.values():
                var.set("")

            # Refrescar combobox de matrículas en pestaña Facturas
            if hasattr(self, "factura_matricula_cb"):
                try:
                    self.factura_matricula_cb.configure(values=self.obtener_matriculas())
                except Exception:
                    pass        
            # Refrescar combobox de matrículas en pestaña Gastos
            if hasattr(self, "gasto_matricula_cb"):
                try:
                    self.gasto_matricula_cb.configure(values=self.obtener_matriculas())
                except Exception:
                    pass

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el coche: {e}")


    # TAB COMPONENTES

    def crear_tab_agregar_componente(self):
        frame = ctk.CTkFrame(self.tab_agregar_componente)
        frame.pack(pady=30)

        # === Sección: Registrar nuevo tipo de componente ===
        ctk.CTkLabel(frame, text="Registrar nuevo tipo de componente", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        labels = ["Nombre:", "Descripción:"]
        self.vars_tipo_comp = {}

        # Campo Nombre
        ctk.CTkLabel(frame, text="Nombre:", font=("Arial", 22)).grid(row=1, column=0, sticky="e", padx=10, pady=6)
        self.vars_tipo_comp["Nombre:"] = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.vars_tipo_comp["Nombre:"], width=250, font=("Arial", 18)).grid(row=1, column=1, padx=10, pady=6)

        # Campo Descripción (multilínea)
        ctk.CTkLabel(frame, text="Descripción:", font=("Arial", 22)).grid(row=2, column=0, sticky="ne", padx=10, pady=6)
        self.descripcion_tipo_componente = ctk.CTkTextbox(frame, width=400, height=120, font=("Arial", 16))
        self.descripcion_tipo_componente.grid(row=2, column=1, padx=10, pady=6)

        # Botón Guardar nuevo tipo
        ctk.CTkButton(frame, text="Añadir tipo de componente", command=self.guardar_tipo_componente).grid(row=3, column=0, columnspan=2, pady=20)

        # === Separador visual ===
        ctk.CTkLabel(frame, text="──────────────────────────────────────────────", font=("Arial", 14)).grid(row=4, column=0, columnspan=2, pady=10)

        # === Sección: Gestión de componentes existentes ===
        ctk.CTkLabel(frame, text="Gestión de tipos de componente existentes", font=("Arial", 18, "bold")).grid(row=5, column=0, columnspan=2, pady=10)

        ctk.CTkLabel(frame, text="Selecciona tipo:", font=("Arial", 22)).grid(row=6, column=0, sticky="e", padx=10, pady=6)
        self.combo_tipo_comp = ttk.Combobox(frame, state="readonly", width=45, values=self.obtener_tipos_componentes())
        self.combo_tipo_comp.grid(row=6, column=1, pady=6)

        # Botones: Cargar, Refrescar, Eliminar
        ctk.CTkButton(frame, text="Cargar datos", hover_color="#515344", command=self.cargar_datos_tipo_componente).grid(row=7, column=0, pady=8)
        ctk.CTkButton(frame, text="Refrescar lista", hover_color="#6168B5", command=lambda: self.combo_tipo_comp.configure(values=self.obtener_tipos_componentes())).grid(row=7, column=1, pady=8)
        ctk.CTkButton(frame, text="Eliminar tipo", fg_color="red", hover_color="#990000", command=self.eliminar_tipo_componente).grid(row=8, column=0, columnspan=2, pady=8)

        # Campos de modificación
        ctk.CTkLabel(frame, text="Nombre:", font=("Arial", 22)).grid(row=9, column=0, sticky="e", padx=10, pady=6)
        self.nombre_tipo_modif = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.nombre_tipo_modif, width=250, font=("Arial", 18)).grid(row=9, column=1, padx=10, pady=6)

        ctk.CTkLabel(frame, text="Descripción:", font=("Arial", 22)).grid(row=10, column=0, sticky="ne", padx=10, pady=6)
        self.descripcion_tipo_modif = ctk.CTkTextbox(frame, width=400, height=120, font=("Arial", 16))
        self.descripcion_tipo_modif.grid(row=10, column=1, padx=10, pady=6)

        # Botón guardar cambios
        ctk.CTkButton(frame, text="Guardar cambios", hover_color="#225A04", command=self.guardar_modificaciones_tipo_componente).grid(row=11, column=0, columnspan=2, pady=16)

        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1)

    def obtener_tipos_componentes(self):
        """Devuelve la lista de tipos de componentes registrados."""
        try:
            cursor = self.conn.execute("SELECT nombre FROM TipoComponente ORDER BY nombre")
            return [row["nombre"] for row in cursor.fetchall()]
        except Exception:
            return []

    def guardar_tipo_componente(self):
        """Guarda un nuevo tipo de componente."""
        nombre = self.vars_tipo_comp["Nombre:"].get().strip()
        descripcion = self.descripcion_tipo_componente.get("1.0", "end").strip()

        if not nombre:
            messagebox.showerror("Error", "El nombre del tipo de componente es obligatorio.")
            return

        try:
            self.conn.execute("INSERT INTO TipoComponente (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Tipo de componente '{nombre}' añadido correctamente.")

            # Refrescar listas
            self.combo_tipo_comp.configure(values=self.obtener_tipos_componentes())
            try:
                self.recargar_tipos_en_producto()
            except Exception as e:
                print(f"No se pudo actualizar el combo de tipos en productos: {e}")
            try:
                self.recargar_tipos_en_mantenimiento()
            except Exception as e:
                print(f"No se pudo actualizar el combo de tipos en mantenimientos: {e}")


            # Limpiar formulario
            self.vars_tipo_comp["Nombre:"].set("")
            self.descripcion_tipo_componente.delete("1.0", "end")

            try:
                # Actualiza el combo aunque la pestaña no esté activa
                tipos = sorted([r["nombre"] for r in self.conn.execute("SELECT * FROM TipoComponente").fetchall()])
                if hasattr(self, "combo_producto_tipo") and self.combo_producto_tipo:
                    self.combo_producto_tipo["values"] = tipos
                    # Refresca el widget visualmente si tiene algún tipo ya seleccionado
                    self.combo_producto_tipo.update()
                print("Combo de productos actualizado con nuevos tipos.")
            except Exception as e:
                print(f"No se pudo actualizar el combo de tipos en productos: {e}")

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ya existe un tipo de componente con ese nombre.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el tipo de componente: {e}")

    def cargar_datos_tipo_componente(self):
        """Carga los datos del tipo seleccionado."""
        nombre_sel = self.combo_tipo_comp.get()
        if not nombre_sel:
            messagebox.showwarning("Atención", "Selecciona un tipo primero.")
            return

        try:
            cursor = self.conn.execute("SELECT * FROM TipoComponente WHERE nombre = ?", (nombre_sel,))
            tipo = cursor.fetchone()
            if tipo:
                self.nombre_tipo_modif.set(tipo["nombre"])
                self.descripcion_tipo_modif.delete("1.0", "end")
                self.descripcion_tipo_modif.insert("1.0", tipo["descripcion"] or "")
            else:
                messagebox.showerror("Error", "No se encontró el tipo seleccionado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")

    def guardar_modificaciones_tipo_componente(self):
        """Guarda los cambios sobre un tipo existente."""
        nombre_original = self.combo_tipo_comp.get()
        if not nombre_original:
            messagebox.showwarning("Atención", "Selecciona un tipo primero.")
            return

        nuevo_nombre = self.nombre_tipo_modif.get().strip()
        nueva_descripcion = self.descripcion_tipo_modif.get("1.0", "end").strip()

        if not nuevo_nombre:
            messagebox.showerror("Error", "El nombre no puede estar vacío.")
            return

        try:
            self.conn.execute(
                "UPDATE TipoComponente SET nombre = ?, descripcion = ? WHERE nombre = ?",
                (nuevo_nombre, nueva_descripcion, nombre_original)
            )
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Tipo de componente '{nuevo_nombre}' actualizado correctamente.")

            # Refrescar combos
            self.combo_tipo_comp.configure(values=self.obtener_tipos_componentes())
            self.combo_tipo_comp.set("")
            self.nombre_tipo_modif.set("")
            self.descripcion_tipo_modif.delete("1.0", "end")

            try:
                self.recargar_tipos_en_mantenimiento()
            except Exception:
                pass

            try:
                self.recargar_tipos_en_producto()
            except Exception as e:
                print(f"No se pudo actualizar el combo de tipos en productos: {e}")

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ya existe un tipo con ese nombre.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los cambios: {e}")

    def eliminar_tipo_componente(self):
        """Elimina el tipo de componente seleccionado."""
        nombre_sel = self.combo_tipo_comp.get()
        if not nombre_sel:
            messagebox.showwarning("Atención", "Selecciona un tipo primero.")
            return

        if not messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de eliminar el tipo '{nombre_sel}'?"):
            return

        try:
            self.conn.execute("DELETE FROM TipoComponente WHERE nombre = ?", (nombre_sel,))
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Tipo de componente '{nombre_sel}' eliminado correctamente.")

            # Refrescar combos y limpiar
            self.combo_tipo_comp.configure(values=self.obtener_tipos_componentes())
            self.combo_tipo_comp.set("")
            self.nombre_tipo_modif.set("")
            self.descripcion_tipo_modif.delete("1.0", "end")

            try:
                self.recargar_tipos_en_mantenimiento()
            except Exception:
                pass

            try:
                self.recargar_tipos_en_producto()
            except Exception as e:
                print(f"No se pudo actualizar el combo de tipos en productos: {e}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el tipo de componente: {e}")


    def recargar_coches_en_mantenimiento(self):
        """Actualiza el combo de coches en la pestaña de mantenimientos."""
        try:
            cursor = self.conn.execute("SELECT matricula, marca, modelo FROM Coche ORDER BY matricula")
            coches = [f"{row['matricula']} ({row['marca']} {row['modelo']})" for row in cursor.fetchall()]
        
            if hasattr(self, "combo_mant_coche"):
                self.combo_mant_coche.set("")
                self.combo_mant_coche['values'] = coches
        except Exception as e:
            print("Error al recargar coches en mantenimientos:", e)

    def recargar_tipos_en_mantenimiento(self):
        """Actualiza el combo de tipos de componente en la pestaña de mantenimientos."""
        try:
            tipos = [row["nombre"] for row in self.conn.execute("SELECT nombre FROM TipoComponente ORDER BY nombre").fetchall()]
            if hasattr(self, "combo_mant_tipo"):
                self.combo_mant_tipo.configure(values=tipos)
                self.combo_mant_tipo.set("")  # opcional: limpia la selección actual
            print("Combo de tipos de mantenimiento actualizado correctamente.")
        except Exception as e:
            print("Error al recargar tipos en mantenimientos:", e)


    # TAB AÑADIR PRODUCTO

    def crear_tab_agregar_producto(self):
        frame_scroll = ctk.CTkScrollableFrame(self.tab_agregar_producto)
        frame_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        frame = ctk.CTkFrame(frame_scroll)
        frame.pack(pady=30)

        def _on_mousewheel(event):
            # Windows / Mac (usa event.delta)
            if event.delta:
                frame_scroll._scrollbar._command("scroll", int(-event.delta / 120), "units")
            # Linux (usa event.num)
            elif event.num == 4:
                frame_scroll._scrollbar._command("scroll", -1, "units")
            elif event.num == 5:
                frame_scroll._scrollbar._command("scroll", 1, "units")

        # Enlaza solo al frame_scroll, no globalmente
        frame_scroll.bind("<Enter>", lambda e: frame_scroll.bind_all("<MouseWheel>", _on_mousewheel))
        frame_scroll.bind("<Leave>", lambda e: frame_scroll.unbind_all("<MouseWheel>"))
        frame_scroll.bind("<Button-4>", _on_mousewheel)  # Linux up
        frame_scroll.bind("<Button-5>", _on_mousewheel)  # Linux down


        ctk.CTkLabel(frame, text="Registrar nuevo producto", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        campos = ["Tipo de componente:", "Marca:", "Modelo:", "Tipo:", "Vida útil (km):", "Vida útil (meses):", "Descripción:"]
        self.vars_producto = {}

        # Creamos el combo vacío, lo rellenamos dinámicamente
        self.combo_producto_tipo = None


        for i, campo in enumerate(campos):
            ctk.CTkLabel(frame, text=campo, font=("Arial", 18)).grid(row=i+1, column=0, sticky="e", padx=10, pady=5)

            if campo == "Descripción:":
                # Área de texto grande para descripción
                txt = ctk.CTkTextbox(frame, width=400, height=100, font=("Arial", 16))
                txt.grid(row=i+1, column=1, padx=10, pady=5)
                self.vars_producto[campo] = txt
            else:
                var = ctk.StringVar()
                self.vars_producto[campo] = var
                if campo == "Tipo de componente:":
                    self.combo_producto_tipo = ttk.Combobox(frame, textvariable=var, state="readonly", width=35, values=self.obtener_tipos_componentes())
                    self.combo_producto_tipo.grid(row=i+1, column=1, padx=10, pady=5)
                else:
                    ctk.CTkEntry(frame, textvariable=var, width=250, font=("Arial", 18)).grid(row=i+1, column=1, padx=10, pady=5)

        ctk.CTkButton(frame, text="Guardar producto", command=self.guardar_producto).grid(
            row=len(campos)+1, column=0, columnspan=2, pady=20
        )


        # SECCIÓN MODIFICAR / ELIMINAR

        ctk.CTkLabel(frame, text="Gestión de productos existentes", font=("Arial", 18, "bold")).grid(
            row=len(campos)+2, column=0, columnspan=2, pady=(30, 10)
        )

        # Frame contenedor horizontal
        gestion_frame = ctk.CTkFrame(frame)
        gestion_frame.grid(row=len(campos)+3, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")
        gestion_frame.grid_columnconfigure((0, 1), weight=1)  # permite que ambas columnas se repartan espacio


        # SUBFRAME IZQUIERDO - MODIFICAR PRODUCTO

        frame_modificar = ctk.CTkFrame(gestion_frame)
        frame_modificar.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        ctk.CTkLabel(frame_modificar, text="Modificar producto", font=("Arial", 16, "bold")).pack(pady=(10, 5))
        self.combo_producto_existente = ttk.Combobox(frame_modificar, state="readonly", width=50)
        self.combo_producto_existente.pack(pady=5)
        self.actualizar_combo_productos()

        ctk.CTkButton(frame_modificar, text="Cargar datos", command=self.cargar_datos_producto).pack(pady=5)

        # Campos para modificación
        self.entry_marca_mod = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Marca")
        self.entry_marca_mod.pack(pady=3)
        self.entry_modelo_mod = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Modelo")
        self.entry_modelo_mod.pack(pady=3)
        self.entry_tipo_mod = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Tipo")
        self.entry_tipo_mod.pack(pady=3)
        self.entry_vidakm_mod = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Vida útil (km)")
        self.entry_vidakm_mod.pack(pady=3)
        self.entry_vidames_mod = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Vida útil (meses)")
        self.entry_vidames_mod.pack(pady=3)
        self.txt_desc_mod = ctk.CTkTextbox(frame_modificar, width=350, height=100, font=("Arial", 14))
        self.txt_desc_mod.pack(pady=5)

        ctk.CTkButton(frame_modificar, text="Guardar cambios", command=self.modificar_producto).pack(pady=10)


        # SUBFRAME DERECHO - ELIMINAR PRODUCTO

        frame_eliminar = ctk.CTkFrame(gestion_frame)
        frame_eliminar.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        ctk.CTkLabel(frame_eliminar, text="Eliminar producto", font=("Arial", 16, "bold")).pack(pady=(10, 5))
        self.combo_eliminar_producto = ttk.Combobox(frame_eliminar, state="readonly", width=50)
        self.combo_eliminar_producto.pack(pady=5)
        self.actualizar_combo_productos_eliminar()

        ctk.CTkButton(frame_eliminar, text="Eliminar producto", fg_color="red", hover_color="#b22222", command=self.eliminar_producto).pack(pady=10)


        # Monitorear cambios de pestaña y actualizar los tipos si se entra en "Añadir producto"
        self.root.after(500, self.verificar_pestana_activa)

    def verificar_pestana_activa(self):
        if self.tabview.get() == "➕ Añadir producto":
            self.recargar_tipos_en_producto()
        elif self.tabview.get() == "➕ Añadir obligaciones":
            self.actualizar_combo_matriculas()  # Refresca matrículas

        self.root.after(500, self.verificar_pestana_activa)

        # Cargar la lista de productos existentes al crear la pestaña
        try:
            self.recargar_productos_existentes()
        except Exception:
            pass

    def actualizar_tipos_componente_en_productos(self, event=None):
        """Refresca los tipos de componente en el combo de productos."""
        if hasattr(self, "vars_producto"):
            tipos = sorted([r["nombre"] for r in self.conn.execute("SELECT * FROM TipoComponente").fetchall()])
            combo = self.tab_agregar_producto.nametowidget(str(self.combo_producto))
            combo["values"] = tipos

    def guardar_producto(self):
        datos = {}
        for k, v in self.vars_producto.items():
            if k == "Descripción:":
                datos[k] = v.get("1.0", "end").strip()
            else:
                datos[k] = v.get().strip()

        if not datos["Tipo de componente:"] or not datos["Marca:"] or not datos["Modelo:"]:
            messagebox.showerror("Error", "Por favor completa todos los campos obligatorios.")
            return

        try:
            id_tipo_row = self.conn.execute(
                "SELECT id_tipo FROM TipoComponente WHERE nombre = ?",
                (datos["Tipo de componente:"],)
            ).fetchone()

            if not id_tipo_row:
                messagebox.showerror("Error", "El tipo de componente seleccionado no existe.")
                return

            id_tipo = id_tipo_row["id_tipo"]
            vida_km = int(datos["Vida útil (km):"]) if datos["Vida útil (km):"] else 0
            vida_meses = int(datos["Vida útil (meses):"]) if datos["Vida útil (meses):"] else 0

            # Insertar y capturar el id del producto recién creado
            cur = self.conn.execute("""
                INSERT INTO Producto (id_tipo, marca, modelo, tipo, descripcion, vida_util_km, vida_util_meses)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                id_tipo,
                datos["Marca:"],
                datos["Modelo:"],
                datos["Tipo:"],
                datos["Descripción:"],
                vida_km,
                vida_meses
            ))
            id_producto_nuevo = cur.lastrowid
            self.conn.commit()
            self.actualizar_combo_producto()

            messagebox.showinfo(
                "Éxito",
                f"Producto '{datos['Marca:']} {datos['Modelo:']} {datos['Tipo:']}' añadido correctamente."
            )

            # Limpiar todos los campos después de guardar
            for k, v in self.vars_producto.items():
                if k == "Descripción:":
                    v.delete("1.0", "end")
                else:
                    v.set("")

            # --- ACTUALIZAR LOS COMBOS AUTOMÁTICAMENTE ---
            self.actualizar_combo_productos()
            self.actualizar_combo_productos_eliminar()

            # --- Seleccionar automáticamente el nuevo producto en los combos ---
            try:
                # Construir la cadena con el mismo formato que usan las funciones de carga
                tipo_nombre = datos["Tipo de componente:"]
                marca = datos["Marca:"]
                modelo = datos["Modelo:"]
                tipo_field = datos["Tipo:"] or ""
                nuevo_label = f"{tipo_nombre} / {marca} {modelo} {tipo_field}"

                # Establecer el valor en ambos combos si existen
                if hasattr(self, "combo_producto_existente"):
                    self.combo_producto_existente.set(nuevo_label)
                if hasattr(self, "combo_eliminar_producto"):
                    self.combo_eliminar_producto.set(nuevo_label)
            except Exception:
                # Si falla la selección automática, no interrumpe la app (los combos ya están actualizados)
                pass

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el producto: {e}")


    def verificar_pestana_activa(self):
        """Comprueba periódicamente si se ha activado la pestaña de 'Añadir producto'."""
        if self.tabview.get() == "➕ Añadir producto":
            self.recargar_tipos_en_producto()
        # Vuelve a comprobar cada 500ms
        self.root.after(500, self.verificar_pestana_activa)
     

    def recargar_tipos_en_producto(self, event=None):
        """Recarga los tipos de componente disponibles al entrar a la pestaña de producto."""
        if self.tabview.get() == "➕ Añadir producto":
            tipos = sorted([r["nombre"] for r in self.conn.execute("SELECT * FROM TipoComponente").fetchall()])
            if self.combo_producto_tipo:
                self.combo_producto_tipo["values"] = tipos

    def actualizar_combo_productos(self):
        """Rellena el combo de modificación con los productos disponibles (sin mostrar ID, orden A–Z)."""
        productos = self.conn.execute("""
            SELECT p.id_producto, tc.nombre AS tipo_componente, p.marca, p.modelo, p.tipo
            FROM Producto p
            JOIN TipoComponente tc ON p.id_tipo = tc.id_tipo
        """).fetchall()

        # Crear el diccionario mapeando texto visible - id_producto
        self.mapa_productos = {
            f"{r['tipo_componente']} / {r['marca']} {r['modelo']} {r['tipo']}": r['id_producto']
            for r in productos
        }

        # Ordenar alfabéticamente los nombres mostrados
        lista = sorted(self.mapa_productos.keys(), key=str.lower)
        self.combo_producto_existente["values"] = lista

    def cargar_datos_producto(self, event=None):
        """Carga los datos del producto seleccionado en los campos de modificación."""
        seleccionado = self.combo_producto_existente.get()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto para modificar.")
            return

        # Recuperar el id_producto directamente del mapa
        id_producto = self.mapa_productos.get(seleccionado)
        if not id_producto:
            messagebox.showerror("Error", "No se pudo identificar el producto seleccionado.")
            return

        try:
            # Obtener el producto desde la base de datos
            row = self.conn.execute(
                "SELECT * FROM Producto WHERE id_producto = ?",
                (id_producto,)
            ).fetchone()

            if not row:
                messagebox.showwarning("Aviso", "No se encontró el producto seleccionado.")
                return

            # Rellenar los campos de edición
            self.entry_marca_mod.delete(0, "end")
            self.entry_marca_mod.insert(0, row["marca"] or "")

            self.entry_modelo_mod.delete(0, "end")
            self.entry_modelo_mod.insert(0, row["modelo"] or "")

            self.entry_tipo_mod.delete(0, "end")
            self.entry_tipo_mod.insert(0, row["tipo"] or "")

            self.entry_vidakm_mod.delete(0, "end")
            self.entry_vidakm_mod.insert(0, str(row["vida_util_km"] or ""))

            self.entry_vidames_mod.delete(0, "end")
            self.entry_vidames_mod.insert(0, str(row["vida_util_meses"] or ""))

            self.txt_desc_mod.delete("1.0", "end")
            self.txt_desc_mod.insert("1.0", row["descripcion"] or "")

            # Registrar el ID actual del producto para la función modificar_producto()
            self.id_producto_actual = id_producto

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos del producto: {e}")


    def modificar_producto(self):
        """Guarda los cambios realizados en un producto existente."""
        if not hasattr(self, "id_producto_actual"):
            messagebox.showwarning("Aviso", "Primero carga un producto antes de modificar.")
            return

        try:
            # --- Leer los datos desde los campos de modificación ---
            marca = self.entry_marca_mod.get().strip()
            modelo = self.entry_modelo_mod.get().strip()
            tipo = self.entry_tipo_mod.get().strip()
            vida_km = self.entry_vidakm_mod.get().strip()
            vida_meses = self.entry_vidames_mod.get().strip()
            descripcion = self.txt_desc_mod.get("1.0", "end").strip()

            # --- Validaciones básicas ---
            if not marca or not modelo:
                messagebox.showwarning("Aviso", "Los campos 'Marca' y 'Modelo' son obligatorios.")
                return

            # --- Recuperar el id_tipo actual del producto ---
            row = self.conn.execute(
                "SELECT id_tipo FROM Producto WHERE id_producto = ?",
                (self.id_producto_actual,)
            ).fetchone()
            if not row:
                messagebox.showerror("Error", "No se encontró el producto a modificar.")
                return

            id_tipo = row["id_tipo"]

            # --- Ejecutar la actualización ---
            self.conn.execute("""
                UPDATE Producto
                SET marca = ?, modelo = ?, tipo = ?, descripcion = ?, 
                    vida_util_km = ?, vida_util_meses = ?
                WHERE id_producto = ?
            """, (
                marca,
                modelo,
                tipo,
                descripcion,
                int(vida_km) if vida_km else 0,
                int(vida_meses) if vida_meses else 0,
                self.id_producto_actual
            ))

            self.conn.commit()

            # --- Mensaje y actualización de combos ---
            messagebox.showinfo("Éxito", f"El producto '{marca} {modelo}' se actualizó correctamente.")
            self.actualizar_combo_productos()
            self.actualizar_combo_productos_eliminar()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar: {e}")


    def actualizar_combo_productos_eliminar(self):
        """Rellena el combo de eliminación con los productos disponibles (sin mostrar ID, igual que el de modificar)."""
        productos = self.conn.execute("""
            SELECT p.id_producto, tc.nombre AS tipo_componente, p.marca, p.modelo, p.tipo
            FROM Producto p
            JOIN TipoComponente tc ON p.id_tipo = tc.id_tipo
        """).fetchall()

        # Crear el diccionario mapeando texto visible - id_producto
        self.mapa_productos_eliminar = {
            f"{r['tipo_componente']} / {r['marca']} {r['modelo']} {r['tipo']}": r['id_producto']
            for r in productos
        }

        # Ordenar alfabéticamente los nombres mostrados
        lista = sorted(self.mapa_productos_eliminar.keys(), key=str.lower)
        self.combo_eliminar_producto["values"] = lista


    def eliminar_producto(self):
        """Elimina el producto seleccionado del combo (usando el id_producto real)."""
        seleccion = self.combo_eliminar_producto.get()
        if not seleccion:
            messagebox.showwarning("Aviso", "Selecciona un producto para eliminar.")
            return

        id_producto = self.mapa_productos_eliminar.get(seleccion)
        if not id_producto:
            messagebox.showerror("Error", "No se pudo identificar el producto seleccionado.")
            return

        confirmar = messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar el producto '{seleccion}'?")
        if confirmar:
            try:
                self.conn.execute("DELETE FROM Producto WHERE id_producto = ?", (id_producto,))
                self.conn.commit()
                messagebox.showinfo("Éxito", f"Producto '{seleccion}' eliminado correctamente.")
                self.actualizar_combo_productos()
                self.actualizar_combo_productos_eliminar()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el producto: {e}")

    def recargar_productos_existentes(self):
        """Recarga y pone en self.combo_producto_existente la lista de productos.
        Formato visible: 'id_producto - Marca Modelo (Tipo)' para distinguirlos."""
        try:
            cursor = self.conn.execute("SELECT id_producto, marca, modelo, tipo FROM Producto ORDER BY marca, modelo")
            productos = [f"{row['id_producto']} - {row['marca']} {row['modelo']} ({row['tipo'] or ''})" for row in cursor.fetchall()]
            if hasattr(self, "combo_producto_existente"):
                self.combo_producto_existente.configure(values=productos)
        except Exception as e:
            print("Error al recargar productos:", e)


    # TAB AÑADIR MANTENIMIENTO

    def crear_tab_agregar_mantenimiento(self):
        frame = ctk.CTkFrame(self.tab_agregar_mantenimiento)
        frame.pack(pady=30)

        ctk.CTkLabel(frame, text="Registrar nuevo mantenimiento", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        # Coche
        ctk.CTkLabel(frame, text="Coche:", font=("Arial", 18)).grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.mant_coche_var = ctk.StringVar()
        coches = [r['matricula'] for r in self.conn.execute("SELECT * FROM Coche").fetchall()]
        self.combo_mant_coche = ttk.Combobox(frame, textvariable=self.mant_coche_var, values=coches, state="readonly", width=35)
        self.combo_mant_coche.grid(row=1, column=1, padx=10, pady=5)

        # Tipo de componente
        ctk.CTkLabel(frame, text="Tipo de componente:", font=("Arial", 18)).grid(row=2, column=0, sticky="e", padx=10, pady=5)
        self.mant_tipo_var = ctk.StringVar()
        tipos = sorted([r['nombre'] for r in self.conn.execute("SELECT * FROM TipoComponente").fetchall()])
        self.combo_mant_tipo = ttk.Combobox(frame, textvariable=self.mant_tipo_var, values=tipos, state="readonly", width=35)
        self.combo_mant_tipo.grid(row=2, column=1, padx=10, pady=5)
        self.combo_mant_tipo.bind("<<ComboboxSelected>>", self.actualizar_combo_producto)

        # Producto
        ctk.CTkLabel(frame, text="Producto:", font=("Arial", 18)).grid(row=3, column=0, sticky="e", padx=10, pady=5)
        self.mant_producto_var = ctk.StringVar()
        self.combo_mant_producto = ttk.Combobox(frame, textvariable=self.mant_producto_var, values=[], state="readonly", width=35)
        self.combo_mant_producto.grid(row=3, column=1, padx=10, pady=5)

        # Fecha y kilómetros
        labels = ["Fecha:", "Kilómetros:"]
        self.vars_mant = {}

        for i, label in enumerate(labels, start=4):
            ctk.CTkLabel(frame, text=label, font=("Arial", 18)).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d") if "Fecha" in label else "")
            self.vars_mant[label] = var
            ctk.CTkEntry(frame, textvariable=var, width=250, font=("Arial", 18)).grid(row=i, column=1, padx=10, pady=5)

        # Descripción (área de texto grande)
        ctk.CTkLabel(frame, text="Descripción:", font=("Arial", 18)).grid(row=6, column=0, sticky="ne", padx=10, pady=5)
        descripcion_textbox = ctk.CTkTextbox(frame, width=400, height=100, font=("Arial", 16))
        descripcion_textbox.grid(row=6, column=1, padx=10, pady=5)
        self.vars_mant["Descripción:"] = descripcion_textbox

        # Botón guardar
        ctk.CTkButton(frame, text="Guardar mantenimiento", command=self.guardar_mantenimiento).grid(row=8, column=0, columnspan=2, pady=20)


        # SECCIÓN: GESTIÓN DE MANTENIMIENTOS

        ctk.CTkLabel(frame, text="Gestión de mantenimientos existentes", font=("Arial", 18, "bold")).grid(
            row=9, column=0, columnspan=2, pady=(30, 10)
        )

        gestion_frame = ctk.CTkFrame(frame)
        gestion_frame.grid(row=10, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")
        gestion_frame.grid_columnconfigure((0, 1), weight=1)


        # SUBFRAME IZQUIERDO - MODIFICAR MANTENIMIENTO

        frame_modificar = ctk.CTkFrame(gestion_frame)
        frame_modificar.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        ctk.CTkLabel(frame_modificar, text="Modificar mantenimiento", font=("Arial", 16, "bold")).pack(pady=(10, 5))
        self.combo_mant_existente = ttk.Combobox(frame_modificar, state="readonly", width=60)
        self.combo_mant_existente.pack(pady=5)
        self.actualizar_combo_mantenimientos()

        ctk.CTkButton(frame_modificar, text="Cargar datos", command=self.cargar_datos_mantenimiento).pack(pady=5)

        # Campos de modificación
        self.entry_mant_fecha = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Fecha (YYYY-MM-DD)")
        self.entry_mant_fecha.pack(pady=3)
        self.entry_mant_km = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Kilómetros")
        self.entry_mant_km.pack(pady=3)
        self.txt_mant_desc = ctk.CTkTextbox(frame_modificar, width=350, height=100, font=("Arial", 14))
        self.txt_mant_desc.pack(pady=5)

        ctk.CTkButton(frame_modificar, text="Guardar cambios", command=self.modificar_mantenimiento).pack(pady=10)


        # SUBFRAME DERECHO - ELIMINAR MANTENIMIENTO

        frame_eliminar = ctk.CTkFrame(gestion_frame)
        frame_eliminar.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        ctk.CTkLabel(frame_eliminar, text="Eliminar mantenimiento", font=("Arial", 16, "bold")).pack(pady=(10, 5))
        self.combo_eliminar_mant = ttk.Combobox(frame_eliminar, state="readonly", width=60)
        self.combo_eliminar_mant.pack(pady=5)
        self.actualizar_combo_mantenimientos_eliminar()

        ctk.CTkButton(frame_eliminar, text="Eliminar mantenimiento", fg_color="red", hover_color="#b22222", command=self.eliminar_mantenimiento).pack(pady=10)


        self.recargar_coches_en_mantenimiento()

        self.combo_mant_coche['values'] = self.obtener_matriculas(mostrar_detalle=True)


    def actualizar_combo_producto(self, event=None):
        tipo_sel = self.mant_tipo_var.get().strip()
        if not tipo_sel:
            self.combo_mant_producto["values"] = []
            return

        cursor = self.conn.execute("""
            SELECT P.marca, P.modelo, T.nombre as tipo_componente
            FROM Producto P
            JOIN TipoComponente T ON P.id_tipo = T.id_tipo
            WHERE LOWER(TRIM(T.nombre)) = LOWER(TRIM(?))
            ORDER BY P.marca, P.modelo
        """, (tipo_sel,))
        productos = [f"{row['marca']}|{row['modelo']}|{row['tipo_componente']}" for row in cursor.fetchall()]

        if productos:
            self.combo_mant_producto["values"] = productos
            self.combo_mant_producto.current(0)
        else:
            self.combo_mant_producto["values"] = []
            self.mant_producto_var.set("")
            messagebox.showinfo("Sin productos", f"No hay productos registrados para '{tipo_sel}'.")

        print(tipo_sel, productos)  # Depuración

    def guardar_mantenimiento(self):
        coche = self.mant_coche_var.get().split(' ')[0]
        producto_str = self.mant_producto_var.get()

        # Para "Descripción", que es un CTkTextbox, hay que usar .get("1.0","end")
        datos = {}
        for k, v in self.vars_mant.items():
            if isinstance(v, ctk.CTkTextbox):  # Área de texto grande
                datos[k] = v.get("1.0", "end").strip()
            else:
                datos[k] = v.get().strip()

        if not (coche and producto_str and datos["Kilómetros:"].isdigit()):
            messagebox.showerror("Error", "Por favor completa todos los campos correctamente.")
            return

        # Extraer marca, modelo y tipo_componente del producto seleccionado
        try:
            marca, modelo, tipo_componente = producto_str.split("|")
        except ValueError:
            messagebox.showerror("Error", "Formato de producto no válido.")
            return

        # Obtener id_producto usando tipo, marca y modelo
        id_producto_row = self.conn.execute("""
            SELECT P.id_producto
            FROM Producto P
            JOIN TipoComponente T ON P.id_tipo = T.id_tipo
            WHERE P.marca = ? AND P.modelo = ? AND T.nombre = ?
        """, (marca, modelo, tipo_componente)).fetchone()

        if not id_producto_row:
            messagebox.showerror("Error", "Producto no encontrado.")
            return

        id_producto = id_producto_row["id_producto"]

        self.conn.execute(
            "INSERT INTO Mantenimiento (matricula, id_producto, fecha, km, descripcion) VALUES (?, ?, ?, ?, ?)",
            (coche, id_producto, datos["Fecha:"], int(datos["Kilómetros:"]), datos["Descripción:"])
        )
        self.conn.commit()
        messagebox.showinfo("Éxito", "Mantenimiento registrado correctamente.")

        # Limpiar campos
        for var in self.vars_mant.values():
            if isinstance(var, ctk.CTkTextbox):
                var.delete("1.0", "end")  # Limpiar área de texto
            else:
                var.set("")  # Limpiar StringVar u otros

        self.mant_coche_var.set("")
        self.mant_tipo_var.set("")
        self.mant_producto_var.set("")

        # Refrescar mantenimientos si se muestra el coche correspondiente
        coche_seleccionado = self.coche_var.get()
        if coche_seleccionado and coche_seleccionado.split(" ")[0] == coche:
            self.mostrar_mantenimientos()

        # Refrescar los combos de mantenimiento (modificar / eliminar)
        self.actualizar_combo_mantenimientos()
        self.actualizar_combo_mantenimientos_eliminar()

        # Seleccionar automáticamente el mantenimiento recién creado
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT M.id_mantenimiento, C.matricula, TC.nombre AS tipo_componente,
                   P.marca, P.modelo, P.tipo, M.fecha
            FROM Mantenimiento M
            LEFT JOIN Coche C ON M.matricula = C.matricula
            LEFT JOIN Producto P ON M.id_producto = P.id_producto
            LEFT JOIN TipoComponente TC ON P.id_tipo = TC.id_tipo
            ORDER BY M.id_mantenimiento DESC
            LIMIT 1
        """)
        ultimo = cursor.fetchone()

        if ultimo:
            texto_combo = f"{ultimo['matricula']} / {ultimo['tipo_componente']}, {ultimo['marca']} {ultimo['modelo']} {ultimo['tipo']} ({ultimo['fecha']})"

            # Actualizar los combos para que incluyan el nuevo registro
            self.actualizar_combo_mantenimientos()
            self.actualizar_combo_mantenimientos_eliminar()

            # Seleccionar automáticamente en ambos combos
            self.combo_mant_existente.set(texto_combo)
            self.combo_eliminar_mant.set(texto_combo)

            # Cargar los datos en el panel de modificación
            self.cargar_datos_mantenimiento()

            
    def recargar_tipos_en_mantenimiento(self):
        tipos = sorted([r['nombre'] for r in self.conn.execute("SELECT * FROM TipoComponente").fetchall()])
        self.combo_mant_tipo['values'] = tipos

    def actualizar_combo_mantenimientos(self):
        """Carga los mantenimientos disponibles en el combo de modificación (sin mostrar el id)."""
        mantenimientos = self.conn.execute("""
            SELECT M.id_mantenimiento, C.matricula, TC.nombre AS tipo_componente,
                P.marca, P.modelo, P.tipo, M.fecha
            FROM Mantenimiento M
            LEFT JOIN Coche C ON M.matricula = C.matricula
            LEFT JOIN Producto P ON M.id_producto = P.id_producto
            LEFT JOIN TipoComponente TC ON P.id_tipo = TC.id_tipo
            ORDER BY C.matricula ASC, M.fecha DESC
        """).fetchall()

        # Crear mapa: texto visible - id_mantenimiento
        self.mapa_mantenimientos = {
            f"{r['matricula']} / {r['tipo_componente']}, {r['marca']} {r['modelo']} {r['tipo']} ({r['fecha']})": r['id_mantenimiento']
            for r in mantenimientos if r['matricula'] and r['tipo_componente']
        }

        # Rellenar el combo ordenado alfabéticamente
        lista = sorted(self.mapa_mantenimientos.keys(), key=str.lower)
        self.combo_mant_existente["values"] = lista


    def cargar_datos_mantenimiento(self):
        """Carga los datos del mantenimiento seleccionado para su modificación."""
        seleccionado = self.combo_mant_existente.get()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un mantenimiento para modificar.")
            return

        id_mant = self.mapa_mantenimientos.get(seleccionado)
        row = self.conn.execute("SELECT * FROM Mantenimiento WHERE id_mantenimiento = ?", (id_mant,)).fetchone()
        if not row:
            messagebox.showerror("Error", "No se encontró el mantenimiento seleccionado.")
            return

        self.entry_mant_fecha.delete(0, "end"); self.entry_mant_fecha.insert(0, row["fecha"])
        self.entry_mant_km.delete(0, "end"); self.entry_mant_km.insert(0, str(row["km"] or ""))
        self.txt_mant_desc.delete("1.0", "end"); self.txt_mant_desc.insert("1.0", row["descripcion"] or "")
        self.id_mant_actual = id_mant

    def modificar_mantenimiento(self):
        """Actualiza los datos del mantenimiento cargado."""
        if not hasattr(self, "id_mant_actual"):
            messagebox.showwarning("Aviso", "Primero carga un mantenimiento antes de modificar.")
            return

        fecha = self.entry_mant_fecha.get().strip()
        km = self.entry_mant_km.get().strip()
        descripcion = self.txt_mant_desc.get("1.0", "end").strip()

        if not fecha:
            messagebox.showerror("Error", "El campo fecha es obligatorio.")
            return

        try:
            self.conn.execute("""
                UPDATE Mantenimiento
                SET fecha = ?, km = ?, descripcion = ?
                WHERE id_mantenimiento = ?
            """, (fecha, int(km) if km else 0, descripcion, self.id_mant_actual))
            self.conn.commit()

            messagebox.showinfo("Éxito", "Mantenimiento actualizado correctamente.")
            self.actualizar_combo_mantenimientos()
            self.actualizar_combo_mantenimientos_eliminar()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar: {e}")

    def actualizar_combo_mantenimientos_eliminar(self):
        """Rellena el combo de eliminación con los mantenimientos disponibles (sin mostrar el id)."""
        mantenimientos = self.conn.execute("""
            SELECT M.id_mantenimiento, C.matricula, TC.nombre AS tipo_componente,
                P.marca, P.modelo, P.tipo, M.fecha
            FROM Mantenimiento M
            LEFT JOIN Coche C ON M.matricula = C.matricula
            LEFT JOIN Producto P ON M.id_producto = P.id_producto
            LEFT JOIN TipoComponente TC ON P.id_tipo = TC.id_tipo
            ORDER BY C.matricula ASC, M.fecha DESC
        """).fetchall()

        # Crear mapa: texto visible - id_mantenimiento
        self.mapa_mant_eliminar = {
            f"{r['matricula']} / {r['tipo_componente']}, {r['marca']} {r['modelo']} {r['tipo']} ({r['fecha']})": r['id_mantenimiento']
            for r in mantenimientos if r['matricula'] and r['tipo_componente']
        }

        lista = sorted(self.mapa_mant_eliminar.keys(), key=str.lower)
        self.combo_eliminar_mant["values"] = lista


    def eliminar_mantenimiento(self):
        """Elimina el mantenimiento seleccionado."""
        seleccion = self.combo_eliminar_mant.get()
        if not seleccion:
            messagebox.showwarning("Aviso", "Selecciona un mantenimiento para eliminar.")
            return

        id_mant = self.mapa_mant_eliminar.get(seleccion)
        confirmar = messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar este mantenimiento?")
        if confirmar:
            self.conn.execute("DELETE FROM Mantenimiento WHERE id_mantenimiento = ?", (id_mant,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Mantenimiento eliminado correctamente.")
            self.actualizar_combo_mantenimientos()
            self.actualizar_combo_mantenimientos_eliminar()

        # --- Refrescar la pestaña "Vehículos" si el coche eliminado está seleccionado ---
        try:
            if hasattr(self, "coche_var") and self.coche_var.get():
                self.mostrar_mantenimientos()
                self.mostrar_gastos_coche()
                self.mostrar_facturas_coche()
        except Exception as e:
            print("Error al refrescar la pestaña Vehículos tras eliminar mantenimiento:", e)



    # TAB OBLIGACIONES
 
    def crear_tab_obligaciones(self):
        frame_scroll = ctk.CTkScrollableFrame(self.tab_obligaciones)
        frame_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        frame = ctk.CTkFrame(frame_scroll)
        frame.pack(pady=30)

        # Scroll suave (soporte Linux / Windows / Mac)
        def _on_mousewheel(event):
            if event.num == 4:
                frame_scroll._parent_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                frame_scroll._parent_canvas.yview_scroll(1, "units")
            else:
                frame_scroll._parent_canvas.yview_scroll(-int(event.delta / 120), "units")
        frame_scroll.bind_all("<MouseWheel>", _on_mousewheel)
        frame_scroll.bind_all("<Button-4>", _on_mousewheel)
        frame_scroll.bind_all("<Button-5>", _on_mousewheel)


        # SECCIÓN: AÑADIR NUEVA OBLIGACIÓN

        ctk.CTkLabel(frame, text="Registrar nueva obligación", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        campos = ["Coche:", "Tipo:", "Descripción:", "Fecha inicio:", "Fecha vencimiento:"]
        self.vars_obligacion = {}

        for i, campo in enumerate(campos):
            ctk.CTkLabel(frame, text=campo, font=("Arial", 16)).grid(row=i+1, column=0, sticky="e", padx=10, pady=5)

            if campo == "Coche:":
                var = ctk.StringVar()
                self.vars_obligacion[campo] = var
                self.obl_coche_cb = ttk.Combobox(frame, textvariable=var, state="readonly", width=35, values=self.obtener_matriculas())
                self.obl_coche_cb.grid(row=i+1, column=1, padx=10, pady=5)

            elif campo == "Tipo:":
                var = ctk.StringVar()
                self.vars_obligacion[campo] = var
                self.obl_tipo_cb = ttk.Combobox(frame, textvariable=var, state="readonly", width=35,
                                                values=["ITV", "Seguro", "Impuesto circulación", "Otros"])
                self.obl_tipo_cb.grid(row=i+1, column=1, padx=10, pady=5)

            elif campo == "Descripción:":
                txt = ctk.CTkTextbox(frame, width=400, height=100, font=("Arial", 14))
                txt.grid(row=i+1, column=1, padx=10, pady=5)
                self.vars_obligacion[campo] = txt

            else:  # Fechas
                var = ctk.StringVar()
                entry = ctk.CTkEntry(frame, textvariable=var, width=200, font=("Arial", 16))
                entry.grid(row=i+1, column=1, padx=10, pady=5)
                self.vars_obligacion[campo] = var

        ctk.CTkButton(frame, text="Guardar obligación", command=self.guardar_obligacion).grid(
            row=len(campos)+2, column=0, columnspan=2, pady=20
        )


        # SECCIÓN: GESTIÓN DE OBLIGACIONES (MODIFICAR / ELIMINAR)

        ctk.CTkLabel(frame, text="Gestión de obligaciones existentes", font=("Arial", 18, "bold")).grid(
            row=len(campos)+3, column=0, columnspan=2, pady=(30, 10)
        )

        gestion_frame = ctk.CTkFrame(frame)
        gestion_frame.grid(row=len(campos)+4, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")
        gestion_frame.grid_columnconfigure((0, 1), weight=1)


        # SUBFRAME IZQUIERDO - MODIFICAR OBLIGACIÓN

        frame_modificar = ctk.CTkFrame(gestion_frame)
        frame_modificar.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        ctk.CTkLabel(frame_modificar, text="Modificar obligación", font=("Arial", 16, "bold")).pack(pady=(10, 5))
        self.combo_obligacion_existente = ttk.Combobox(frame_modificar, state="readonly", width=50)
        self.combo_obligacion_existente.pack(pady=5)
        self.actualizar_combo_obligaciones()

        ctk.CTkButton(frame_modificar, text="Cargar datos", command=self.cargar_datos_obligacion).pack(pady=5)

        # Campos de modificación
        self.entry_tipo_mod_obl = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Tipo")
        self.entry_tipo_mod_obl.pack(pady=3)
        self.entry_inicio_mod_obl = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Fecha inicio (YYYY-MM-DD)")
        self.entry_inicio_mod_obl.pack(pady=3)
        self.entry_venc_mod_obl = ctk.CTkEntry(frame_modificar, width=250, font=("Arial", 16), placeholder_text="Fecha vencimiento (YYYY-MM-DD)")
        self.entry_venc_mod_obl.pack(pady=3)
        self.txt_desc_mod_obl = ctk.CTkTextbox(frame_modificar, width=350, height=100, font=("Arial", 14))
        self.txt_desc_mod_obl.pack(pady=5)

        ctk.CTkButton(frame_modificar, text="Guardar cambios", command=self.modificar_obligacion).pack(pady=10)


        # SUBFRAME DERECHO - ELIMINAR OBLIGACIÓN

        frame_eliminar = ctk.CTkFrame(gestion_frame)
        frame_eliminar.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        ctk.CTkLabel(frame_eliminar, text="Eliminar obligación", font=("Arial", 16, "bold")).pack(pady=(10, 5))
        self.combo_eliminar_obligacion = ttk.Combobox(frame_eliminar, state="readonly", width=50)
        self.combo_eliminar_obligacion.pack(pady=5)
        self.actualizar_combo_obligaciones_eliminar()

        ctk.CTkButton(frame_eliminar, text="Eliminar obligación", fg_color="red", hover_color="#b22222",
                      command=self.eliminar_obligacion).pack(pady=10)
        

    def guardar_obligacion(self):
        datos = {}
        for k, v in self.vars_obligacion.items():
            if k == "Descripción:":
                datos[k] = v.get("1.0", "end").strip()
            else:
                datos[k] = v.get().strip()

        if not datos["Coche:"] or not datos["Tipo:"]:
            messagebox.showerror("Error", "Por favor, selecciona un coche y tipo de obligación.")
            return

        try:
            self.conn.execute("""
                INSERT INTO Obligaciones (matricula, tipo, descripcion, fecha_inicio, fecha_vencimiento)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datos["Coche:"],
                datos["Tipo:"],
                datos["Descripción:"],
                datos["Fecha inicio:"],
                datos["Fecha vencimiento:"]
            ))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Obligación guardada correctamente.")
            self.actualizar_combo_obligaciones()
            self.actualizar_combo_obligaciones_eliminar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la obligación: {e}")


    def actualizar_combo_obligaciones(self):
        obligaciones = self.conn.execute("""
            SELECT id_obligacion, matricula, tipo, fecha_vencimiento
            FROM Obligaciones ORDER BY fecha_vencimiento DESC
        """).fetchall()

        self.mapa_obligaciones = {
            f"{r['matricula']} - {r['tipo']} (vence {r['fecha_vencimiento']})": r["id_obligacion"]
            for r in obligaciones
        }
        self.combo_obligacion_existente["values"] = sorted(self.mapa_obligaciones.keys())


    def cargar_datos_obligacion(self):
        seleccion = self.combo_obligacion_existente.get()
        if not seleccion:
            messagebox.showwarning("Aviso", "Selecciona una obligación para modificar.")
            return
        id_obl = self.mapa_obligaciones.get(seleccion)
        row = self.conn.execute("SELECT * FROM Obligaciones WHERE id_obligacion = ?", (id_obl,)).fetchone()
        if not row:
            messagebox.showerror("Error", "No se encontró la obligación seleccionada.")
            return
        self.entry_tipo_mod_obl.delete(0, "end")
        self.entry_tipo_mod_obl.insert(0, row["tipo"])
        self.entry_inicio_mod_obl.delete(0, "end")
        self.entry_inicio_mod_obl.insert(0, row["fecha_inicio"])
        self.entry_venc_mod_obl.delete(0, "end")
        self.entry_venc_mod_obl.insert(0, row["fecha_vencimiento"])
        self.txt_desc_mod_obl.delete("1.0", "end")
        self.txt_desc_mod_obl.insert("1.0", row["descripcion"])
        self.id_obligacion_actual = id_obl


    def modificar_obligacion(self):
        if not hasattr(self, "id_obligacion_actual"):
            messagebox.showwarning("Aviso", "Primero carga una obligación antes de modificar.")
            return
        try:
            self.conn.execute("""
                UPDATE Obligaciones
                SET tipo=?, descripcion=?, fecha_inicio=?, fecha_vencimiento=?
                WHERE id_obligacion=?
            """, (
                self.entry_tipo_mod_obl.get().strip(),
                self.txt_desc_mod_obl.get("1.0", "end").strip(),
                self.entry_inicio_mod_obl.get().strip(),
                self.entry_venc_mod_obl.get().strip(),
                self.id_obligacion_actual
            ))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Obligación actualizada correctamente.")
            self.actualizar_combo_obligaciones()
            self.actualizar_combo_obligaciones_eliminar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la obligación: {e}")


    def actualizar_combo_obligaciones_eliminar(self):
        obligaciones = self.conn.execute("""
            SELECT id_obligacion, matricula, tipo, fecha_vencimiento
            FROM Obligaciones ORDER BY fecha_vencimiento DESC
        """).fetchall()
        self.mapa_obligaciones_eliminar = {
            f"{r['matricula']} - {r['tipo']} (vence {r['fecha_vencimiento']})": r["id_obligacion"]
            for r in obligaciones
        }
        self.combo_eliminar_obligacion["values"] = sorted(self.mapa_obligaciones_eliminar.keys())


    def eliminar_obligacion(self):
        seleccion = self.combo_eliminar_obligacion.get()
        if not seleccion:
            messagebox.showwarning("Aviso", "Selecciona una obligación para eliminar.")
            return
        id_obl = self.mapa_obligaciones_eliminar.get(seleccion)
        confirmar = messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar '{seleccion}'?")
        if confirmar:
            self.conn.execute("DELETE FROM Obligaciones WHERE id_obligacion = ?", (id_obl,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Obligación eliminada correctamente.")
            self.actualizar_combo_obligaciones()
            self.actualizar_combo_obligaciones_eliminar()


    # PESTAÑA PROVEEDORES

    def crear_tab_proveedores(self):

        tab = self.tab_proveedores

        # Frame superior: formulario
        frame_form = ctk.CTkFrame(tab)
        frame_form.pack(fill="x", padx=20, pady=10)

        labels = ["Nombre", "CIF/NIF", "Tipo", "Teléfono", "Email", "Dirección", "Descripción"]
        self.entries_prov = {}

        for i, label_text in enumerate(labels):
            ctk.CTkLabel(frame_form, text=label_text + ":").grid(row=i, column=0, sticky="w", pady=3)
            entry = ctk.CTkEntry(frame_form, width=400)
            entry.grid(row=i, column=1, pady=3, padx=5)
            claves_bd = ["nombre", "cif_nif", "tipo", "telefono", "email", "direccion", "descripcion"]
            for i, (label_text, clave) in enumerate(zip(labels, claves_bd)):
                ctk.CTkLabel(frame_form, text=label_text + ":").grid(row=i, column=0, sticky="w", pady=3)
                entry = ctk.CTkEntry(frame_form, width=400)
                entry.grid(row=i, column=1, pady=3, padx=5)
                self.entries_prov[clave] = entry


        # Botones de acción
        frame_btns = ctk.CTkFrame(frame_form)
        frame_btns.grid(row=len(labels), column=0, columnspan=2, pady=10)

        ctk.CTkButton(frame_btns, text="Guardar", command=self.guardar_proveedor).grid(row=0, column=0, padx=5)
        ctk.CTkButton(frame_btns, text="Eliminar", command=self.eliminar_proveedor).grid(row=0, column=1, padx=5)
        ctk.CTkButton(frame_btns, text="Limpiar", command=self.limpiar_form_proveedor).grid(row=0, column=2, padx=5)

        # Tabla Treeview (usamos ttk.Treeview porque CTk no tiene tabla)
        frame_tabla = ctk.CTkFrame(tab)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)

        columnas = ("id", "nombre", "cif_nif", "tipo", "telefono", "email", "direccion", "descripcion")
        self.tree_proveedores = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=10)

        for col in columnas:
            self.tree_proveedores.heading(col, text=col.capitalize())
            self.tree_proveedores.column(col, width=140, anchor="center")

        self.tree_proveedores.pack(fill="both", expand=True, pady=10)
        self.tree_proveedores.bind("<<TreeviewSelect>>", self.seleccionar_proveedor)

        self.actualizar_tabla_proveedores()


    def actualizar_tabla_proveedores(self):
        for fila in self.tree_proveedores.get_children():
            self.tree_proveedores.delete(fila)

        cursor = self.conn.execute("SELECT * FROM Proveedor ORDER BY id_proveedor")
        for fila in cursor.fetchall():
            self.tree_proveedores.insert("", "end", values=tuple(fila))


    def guardar_proveedor(self):
        datos = {k: v.get().strip() for k, v in self.entries_prov.items()}
        if not datos["nombre"]:
            messagebox.showwarning("Atención", "El nombre es obligatorio.")
            return

        item_sel = self.tree_proveedores.selection()
        if item_sel:
            id_sel = self.tree_proveedores.item(item_sel[0], "values")[0]
            self.conn.execute("""
                UPDATE Proveedor
                SET nombre=?, cif_nif=?, tipo=?, telefono=?, email=?, direccion=?, descripcion=?
                WHERE id_proveedor=?
            """, (
                datos["nombre"], datos["cif_nif"], datos["tipo"], datos["telefono"],
                datos["email"], datos["direccion"], datos["descripcion"], id_sel
            ))
            self.conn.commit()
        else:
            cursor = self.conn.execute("""
                INSERT INTO Proveedor (nombre, cif_nif, tipo, telefono, email, direccion, descripcion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datos["nombre"], datos["cif_nif"], datos["tipo"], datos["telefono"],
                datos["email"], datos["direccion"], datos["descripcion"]
            ))
            self.conn.commit()

            # Selecciona automáticamente el nuevo
            nuevo_id = cursor.lastrowid
            self.actualizar_tabla_proveedores()
            for item in self.tree_proveedores.get_children():
                if self.tree_proveedores.item(item, "values")[0] == str(nuevo_id):
                    self.tree_proveedores.selection_set(item)
                    self.tree_proveedores.focus(item)
                    self.tree_proveedores.see(item)
                    break

        self.actualizar_tabla_proveedores()
        messagebox.showinfo("Éxito", "Proveedor guardado correctamente.")

        self.recargar_proveedores_en_facturas()

    def seleccionar_proveedor(self, event):
        item_sel = self.tree_proveedores.selection()
        if not item_sel:
            return
        datos = self.tree_proveedores.item(item_sel[0], "values")
        claves = ["nombre", "cif_nif", "tipo", "telefono", "email", "direccion", "descripcion"]
        for clave, valor in zip(claves, datos[1:]):  # omite id
            self.entries_prov[clave].delete(0, "end")
            self.entries_prov[clave].insert(0, valor)


    def eliminar_proveedor(self):
        item_sel = self.tree_proveedores.selection()
        if not item_sel:
            messagebox.showwarning("Atención", "Selecciona un proveedor para eliminar.")
            return

        id_sel = self.tree_proveedores.item(item_sel[0], "values")[0]
        confirmar = messagebox.askyesno("Confirmar", "¿Eliminar este proveedor?")
        if confirmar:
            self.conn.execute("DELETE FROM Proveedor WHERE id_proveedor=?", (id_sel,))
            self.conn.commit()
            self.actualizar_tabla_proveedores()
            self.limpiar_form_proveedor()
            self.recargar_proveedores_en_facturas()


    def limpiar_form_proveedor(self):
        for entry in self.entries_prov.values():
            entry.delete(0, "end")
        self.tree_proveedores.selection_remove(self.tree_proveedores.selection())

    def recargar_proveedores_en_facturas(self):
        cursor = self.conn.execute("SELECT id_proveedor, nombre FROM Proveedor ORDER BY nombre")
        proveedores = cursor.fetchall()

        # Actualizamos dict
        self.proveedor_dict = {p["nombre"]: p["id_proveedor"] for p in proveedores}

        # Actualizamos combobox
        self.factura_proveedor_cb["values"] = list(self.proveedor_dict.keys())


    # PESTAÑA FACTURAS

    def crear_tab_facturas(self):

        frame = ctk.CTkScrollableFrame(self.tab_facturas)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Título ---
        ctk.CTkLabel(frame, text="Gestión de Facturas", font=("Arial", 20, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )

        # --- Obtener matrículas ---
        cursor = self.conn.execute("SELECT matricula FROM Coche ORDER BY matricula")
        matriculas = [row["matricula"] for row in cursor.fetchall()]

        # --- Obtener proveedores ---
        cursor = self.conn.execute("SELECT id_proveedor, nombre FROM Proveedor ORDER BY nombre")
        proveedores = cursor.fetchall()
        self.proveedor_dict = {p["nombre"]: p["id_proveedor"] for p in proveedores}

        # --- Variables de los campos ---
        self.factura_vars = {
            "id_factura": None,
            "id_proveedor": ctk.StringVar(),
            "num_factura": ctk.StringVar(),
            "fecha_emision": ctk.StringVar(),
            "importe_total": ctk.StringVar(),
            "matricula": ctk.StringVar()
        }

        # --- Selector de vehículo ---
        ctk.CTkLabel(frame, text="Vehículo (Matrícula):", font=("Arial", 16)).grid(
            row=1, column=0, sticky="e", padx=10, pady=5
        )
        self.factura_matricula_cb = ttk.Combobox(
            frame,
            textvariable=self.factura_vars["matricula"],
            values=matriculas,
            state="readonly",
            width=40
        )
        self.factura_matricula_cb.grid(row=1, column=1, padx=10, pady=5)

        # --- Selector de proveedor ---
        ctk.CTkLabel(frame, text="Proveedor:", font=("Arial", 16)).grid(
            row=2, column=0, sticky="e", padx=10, pady=5
        )
        self.factura_proveedor_cb = ttk.Combobox(
            frame,
            textvariable=self.factura_vars["id_proveedor"],
            values=list(self.proveedor_dict.keys()),
            state="readonly",
            width=40
        )
        self.factura_proveedor_cb.grid(row=2, column=1, padx=10, pady=5)

        # --- Nº de factura ---
        ctk.CTkLabel(frame, text="Nº Factura:", font=("Arial", 16)).grid(
            row=3, column=0, sticky="e", padx=10, pady=5
        )
        ctk.CTkEntry(frame, textvariable=self.factura_vars["num_factura"], width=250).grid(
            row=3, column=1, padx=10, pady=5
        )

        # --- Fecha de emisión ---
        ctk.CTkLabel(frame, text="Fecha emisión:", font=("Arial", 16)).grid(
            row=4, column=0, sticky="e", padx=10, pady=5
        )
        ctk.CTkEntry(frame, textvariable=self.factura_vars["fecha_emision"], width=250).grid(
            row=4, column=1, padx=10, pady=5
        )   

        # --- Importe total ---
        ctk.CTkLabel(frame, text="Importe total (€):", font=("Arial", 16)).grid(
            row=5, column=0, sticky="e", padx=10, pady=5
        )
        ctk.CTkEntry(frame, textvariable=self.factura_vars["importe_total"], width=250).grid(
            row=5, column=1, padx=10, pady=5
        )

        # --- Botonera centrada ---
        botones_frame = ctk.CTkFrame(frame)
        botones_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ctk.CTkButton(botones_frame, text="Guardar / Modificar", command=self.guardar_factura).grid(row=0, column=0, padx=10)
        ctk.CTkButton(botones_frame, text="Eliminar", fg_color="red", command=self.eliminar_factura).grid(row=0, column=1, padx=10)
        ctk.CTkButton(botones_frame, text="Limpiar", command=self.limpiar_form_factura).grid(row=0, column=2, padx=10)

        # --- Listado de facturas ---
        self.tree_facturas = ttk.Treeview(
            frame,
            columns=("id", "proveedor", "num", "fecha", "importe", "matricula"),
            show="headings",
            height=10
        )
        self.tree_facturas.grid(row=7, column=0, columnspan=2, pady=10)

        for col, title in zip(("id", "proveedor", "num", "fecha", "importe", "matricula"),
                            ("ID", "Proveedor", "Nº Factura", "Fecha", "Importe €", "Matrícula")):
            self.tree_facturas.heading(col, text=title)
            self.tree_facturas.column(col, width=130)

        self.tree_facturas.bind("<<TreeviewSelect>>", self.seleccionar_factura)

        # --- Cargar datos iniciales ---
        self.actualizar_tabla_facturas()

        # --- Centrado visual general ---
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)


    def actualizar_tabla_facturas(self):
        """Carga todas las facturas en la tabla."""
        for fila in self.tree_facturas.get_children():
            self.tree_facturas.delete(fila)

        query = """
            SELECT f.id_factura, p.nombre AS proveedor, f.num_factura, f.fecha_emision, f.importe_total, f.matricula
            FROM Factura f
            JOIN Proveedor p ON f.id_proveedor = p.id_proveedor
            ORDER BY substr(f.fecha_emision, 7, 4) || '-' || substr(f.fecha_emision, 4, 2) || '-' || substr(f.fecha_emision, 1, 2) DESC
        """
        for row in self.conn.execute(query).fetchall():
            self.tree_facturas.insert("", "end", values=(row["id_factura"], row["proveedor"], row["num_factura"], row["fecha_emision"], row["importe_total"], row["matricula"]))


    def guardar_factura(self):
        """Guarda o modifica una factura, asignándola opcionalmente a un vehículo."""
        proveedor_nombre = self.factura_vars["id_proveedor"].get()
        id_proveedor = self.proveedor_dict.get(proveedor_nombre)

        matricula = self.factura_vars["matricula"].get().strip()
        num_factura = self.factura_vars["num_factura"].get().strip()
        fecha = self.factura_vars["fecha_emision"].get().strip()
        importe = self.factura_vars["importe_total"].get().strip()

        if not id_proveedor or not num_factura:
            messagebox.showwarning("Atención", "Proveedor y Nº de factura son obligatorios.")
            return

        try:
            importe_valor = float(importe) if importe else 0.0
        except ValueError:
            messagebox.showwarning("Error", "El importe debe ser un número válido.")
            return

        seleccion = self.tree_facturas.selection()
        if seleccion:
            id_factura = self.tree_facturas.item(seleccion[0], "values")[0]
            self.conn.execute("""
                UPDATE Factura
                SET id_proveedor=?, num_factura=?, fecha_emision=?, importe_total=?, matricula=?
                WHERE id_factura=?
            """, (id_proveedor, num_factura, fecha, importe_valor, matricula, id_factura))
            self.conn.commit()
            messagebox.showinfo("Actualizado", "Factura modificada correctamente.")
        else:
            cursor = self.conn.execute("""
                INSERT INTO Factura (id_proveedor, num_factura, fecha_emision, importe_total, matricula)
                VALUES (?, ?, ?, ?, ?)
            """, (id_proveedor, num_factura, fecha, importe_valor, matricula))
            self.conn.commit()
            nuevo_id = cursor.lastrowid
            messagebox.showinfo("Éxito", f"Factura registrada (ID {nuevo_id}).")

        self.actualizar_tabla_facturas()
        self.limpiar_form_factura()
        self.mostrar_facturas_coche()

        # Refrescar combobox de facturas en pestaña Gastos
        if hasattr(self, "gasto_factura_cb"):
            try:
                cursor_fact = self.conn.execute("SELECT id_factura, num_factura FROM Factura ORDER BY fecha_emision DESC")
                facturas = [f"{row['id_factura']} - {row['num_factura']}" for row in cursor_fact.fetchall()]
                self.gasto_factura_cb.configure(values=facturas)
            except Exception:
                pass

    def seleccionar_factura(self, event):
        """Carga los datos de la factura seleccionada en el formulario."""
        item_sel = self.tree_facturas.selection()
        if not item_sel:
            return
        datos = self.tree_facturas.item(item_sel[0], "values")

        self.factura_vars["id_factura"] = datos[0]
        self.factura_vars["id_proveedor"].set(datos[1])  # Nombre del proveedor
        self.factura_vars["num_factura"].set(datos[2])
        self.factura_vars["fecha_emision"].set(datos[3])
        self.factura_vars["importe_total"].set(datos[4])
        self.factura_vars["matricula"].set(datos[5])


    def eliminar_factura(self):
        """Elimina la factura seleccionada."""
        item_sel = self.tree_facturas.selection()
        if not item_sel:
            messagebox.showwarning("Atención", "Selecciona una factura para eliminar.")
            return

        id_sel = self.tree_facturas.item(item_sel[0], "values")[0]
        confirmar = messagebox.askyesno("Confirmar", "¿Eliminar esta factura?")
        if confirmar:
            self.conn.execute("DELETE FROM Factura WHERE id_factura=?", (id_sel,))
            self.conn.commit()
            self.actualizar_tabla_facturas()
            self.limpiar_form_factura()
            self.mostrar_facturas_coche()

            # --- Refrescar combobox de facturas en pestaña Gastos ---
            if hasattr(self, "gasto_factura_cb"):
                try:
                    cursor_fact = self.conn.execute(
                        "SELECT id_factura, num_factura FROM Factura ORDER BY fecha_emision DESC"
                    )
                    facturas = [f"{row['id_factura']} - {row['num_factura']}" for row in cursor_fact.fetchall()]
                    self.gasto_factura_cb.configure(values=facturas)
                except Exception:
                    pass

            messagebox.showinfo("Eliminada", "Factura eliminada correctamente.")


    def limpiar_form_factura(self):
        """Limpia el formulario y deselecciona la tabla."""
        for var in self.factura_vars.values():
            if isinstance(var, ctk.StringVar):
                var.set("")
        self.tree_facturas.selection_remove(self.tree_facturas.selection())


    # TAB GASTOS
    
    def crear_tab_gastos(self):
    
        frame = ctk.CTkScrollableFrame(self.tab_gastos)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Título ---
        ctk.CTkLabel(frame, text="Gestión de Gastos", font=("Arial", 20, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )

        # --- Obtener datos para combos ---
        matriculas = self.obtener_matriculas()
        cursor_fact = self.conn.execute("SELECT id_factura, num_factura FROM Factura ORDER BY fecha_emision DESC")
        facturas = [f"{row['id_factura']} - {row['num_factura']}" for row in cursor_fact.fetchall()]

        # --- Variables ---
        self.gasto_vars = {
            "id_gasto": None,
            "matricula": ctk.StringVar(),
            "id_factura": ctk.StringVar(),
            "fecha": ctk.StringVar(),
            "categoria": ctk.StringVar(),
            "concepto": ctk.StringVar(),
            "importe": ctk.StringVar(),
            "observaciones": ctk.StringVar()
        }

        # --- Campos del formulario ---
        ctk.CTkLabel(frame, text="Vehículo (Matrícula):", font=("Arial", 16)).grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.gasto_matricula_cb = ttk.Combobox(frame, textvariable=self.gasto_vars["matricula"], values=matriculas, state="readonly", width=40)
        self.gasto_matricula_cb.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Factura (opcional):", font=("Arial", 16)).grid(row=2, column=0, sticky="e", padx=10, pady=5)
        self.gasto_factura_cb = ttk.Combobox(frame, textvariable=self.gasto_vars["id_factura"], values=facturas, state="readonly", width=40)
        self.gasto_factura_cb.grid(row=2, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Fecha:", font=("Arial", 16)).grid(row=3, column=0, sticky="e", padx=10, pady=5)
        ctk.CTkEntry(frame, textvariable=self.gasto_vars["fecha"], width=250).grid(row=3, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Categoría:", font=("Arial", 16)).grid(row=4, column=0, sticky="e", padx=10, pady=5)
        ctk.CTkEntry(frame, textvariable=self.gasto_vars["categoria"], width=250).grid(row=4, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Concepto:", font=("Arial", 16)).grid(row=5, column=0, sticky="e", padx=10, pady=5)
        ctk.CTkEntry(frame, textvariable=self.gasto_vars["concepto"], width=250).grid(row=5, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Importe (€):", font=("Arial", 16)).grid(row=6, column=0, sticky="e", padx=10, pady=5)
        ctk.CTkEntry(frame, textvariable=self.gasto_vars["importe"], width=250).grid(row=6, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Observaciones:", font=("Arial", 16)).grid(row=7, column=0, sticky="e", padx=10, pady=5)
        ctk.CTkEntry(frame, textvariable=self.gasto_vars["observaciones"], width=250).grid(row=7, column=1, padx=10, pady=5)

        # --- Botones ---
        botones_frame = ctk.CTkFrame(frame)
        botones_frame.grid(row=8, column=0, columnspan=2, pady=20)
        ctk.CTkButton(botones_frame, text="Guardar / Modificar", command=self.guardar_gasto).grid(row=0, column=0, padx=10)
        ctk.CTkButton(botones_frame, text="Eliminar", fg_color="red", command=self.eliminar_gasto).grid(row=0, column=1, padx=10)
        ctk.CTkButton(botones_frame, text="Limpiar", command=self.limpiar_form_gasto).grid(row=0, column=2, padx=10)

        # --- Tabla de gastos ---
        self.tree_gastos = ttk.Treeview(
            frame,
            columns=("id", "matricula", "factura", "fecha", "categoria", "concepto", "importe"),
            show="headings",
            height=10
        )
        self.tree_gastos.grid(row=9, column=0, columnspan=2, pady=10)

        for col, title in zip(
            ("id", "matricula", "factura", "fecha", "categoria", "concepto", "importe"),
            ("ID", "Vehículo", "Factura", "Fecha", "Categoría", "Concepto", "Importe €")
        ):
            self.tree_gastos.heading(col, text=title)
            self.tree_gastos.column(col, width=130)

        self.tree_gastos.bind("<<TreeviewSelect>>", self.seleccionar_gasto)

        self.actualizar_tabla_gastos()

        # --- Centrar contenido ---
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def actualizar_tabla_gastos(self):
        for fila in self.tree_gastos.get_children():
            self.tree_gastos.delete(fila)

        query = """
            SELECT g.id_gasto, g.matricula, f.num_factura AS factura, g.fecha, g.categoria, g.concepto, g.importe
            FROM Gasto g
            LEFT JOIN Factura f ON g.id_factura = f.id_factura
            ORDER BY g.fecha DESC
        """
        for row in self.conn.execute(query).fetchall():
            self.tree_gastos.insert("", "end", values=tuple(row))

    def guardar_gasto(self):
        datos = {k: v.get().strip() for k, v in self.gasto_vars.items() if k != "id_gasto"}

        if not datos["matricula"] or not datos["concepto"] or not datos["importe"]:
            messagebox.showwarning("Atención", "Matrícula, concepto e importe son obligatorios.")
            return

        id_factura = datos["id_factura"].split(" - ")[0] if datos["id_factura"] else None

        item_sel = self.tree_gastos.selection()
        if item_sel:
            id_sel = self.tree_gastos.item(item_sel[0], "values")[0]
            self.conn.execute("""
                UPDATE Gasto SET matricula=?, id_factura=?, fecha=?, categoria=?, concepto=?, importe=?, observaciones=?
                WHERE id_gasto=?
            """, (datos["matricula"], id_factura, datos["fecha"], datos["categoria"],
                datos["concepto"], datos["importe"], datos["observaciones"], id_sel))
        else:
            self.conn.execute("""
                INSERT INTO Gasto (matricula, id_factura, fecha, categoria, concepto, importe, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (datos["matricula"], id_factura, datos["fecha"], datos["categoria"],
                  datos["concepto"], datos["importe"], datos["observaciones"]))
        self.conn.commit()
        self.actualizar_tabla_gastos()
        messagebox.showinfo("Éxito", "Gasto guardado correctamente.")
        # --- Refrescar gastos en pestaña Vehículos si está activa ---
        try:
            if hasattr(self, "coche_var") and self.coche_var.get():
                self.mostrar_gastos_coche()
        except Exception as e:
            print("No se pudo refrescar la vista de gastos:", e)


    def seleccionar_gasto(self, event):
        item_sel = self.tree_gastos.selection()
        if not item_sel:
            return
        datos = self.tree_gastos.item(item_sel[0], "values")

        self.gasto_vars["matricula"].set(datos[1])
        self.gasto_vars["id_factura"].set(datos[2] or "")
        self.gasto_vars["fecha"].set(datos[3] or "")
        self.gasto_vars["categoria"].set(datos[4] or "")
        self.gasto_vars["concepto"].set(datos[5] or "")
        self.gasto_vars["importe"].set(datos[6] or "")
        self.gasto_vars["observaciones"].set("")

    def eliminar_gasto(self):
        item_sel = self.tree_gastos.selection()
        if not item_sel:
            messagebox.showwarning("Atención", "Selecciona un gasto para eliminar.")
            return
        id_sel = self.tree_gastos.item(item_sel[0], "values")[0]
        if messagebox.askyesno("Confirmar", "¿Eliminar este gasto?"):
            self.conn.execute("DELETE FROM Gasto WHERE id_gasto=?", (id_sel,))
            self.conn.commit()
            self.actualizar_tabla_gastos()
            self.limpiar_form_gasto()
                # --- Refrescar gastos en pestaña Vehículos si está activa ---
        try:
            if hasattr(self, "coche_var") and self.coche_var.get():
                self.mostrar_gastos_coche()
        except Exception as e:
            print("No se pudo refrescar la vista de gastos:", e)

    def limpiar_form_gasto(self):
        for var in self.gasto_vars.values():
            if isinstance(var, ctk.StringVar):
                var.set("")
        self.tree_gastos.selection_remove(self.tree_gastos.selection())


    # FUNCIONES BASE DE DATOS Y PDF

    def cargar_coches(self):
        """Carga la lista de coches en el combo principal, sin seleccionar ninguno al inicio."""
        cursor = self.conn.execute("SELECT matricula, marca, modelo FROM Coche ORDER BY matricula")
        coches = [f"{row['matricula']} ({row['marca']} {row['modelo']})" for row in cursor.fetchall()]
        self.combo_coche['values'] = coches

        # Limpia la selección visualmente (aunque haya vehículos)
        self.combo_coche.set("")  
        self.coche_var.set("")  

        # Limpia también la tabla de mantenimientos
        for widget in self.frame_mantenimientos.winfo_children():
            widget.destroy()

        # Limpia los datos de info y km
        self.fecha_mat_var.set("—")
        self.km_var.set("")


    def mostrar_mantenimientos(self, event=None):
        # Limpiar el frame
        for widget in self.frame_mantenimientos.winfo_children():
            widget.destroy()

        coche_seleccionado = self.coche_var.get()
        if not coche_seleccionado:
            return
        matricula = coche_seleccionado.split(" ")[0]

        # Mostrar título de sección
        ctk.CTkLabel(self.frame_mantenimientos, text="Mantenimientos", font=("Arial", 20, "bold"))\
            .grid(row=0, column=0, columnspan=6, pady=(0, 10))

        # Obtener kilómetros actuales del vehículo
        cursor = self.conn.execute("SELECT km_actuales, fecha_matriculacion FROM Coche WHERE matricula = ?", (matricula,))
        row = cursor.fetchone()
        if row:
            self.km_var.set(row["km_actuales"] or 0)
            self.fecha_mat_var.set(row["fecha_matriculacion"] or "—")
        else:
            self.km_var.set(0)
            self.fecha_mat_var.set("—")

        # Encabezados de tabla (empezamos en fila 1 porque fila 0 es el título)
        headers = ["Elemento (Tipo)", "Fecha", "Km", "Próx. cambio (km)", "Próx. cambio (fecha)", "Descripción"]
        for col, h in enumerate(headers):
            ctk.CTkLabel(self.frame_mantenimientos, text=h, font=("Arial", 16, "bold"))\
                .grid(row=1, column=col, padx=5, pady=3)

        # --- Mostrar mantenimientos ---
        cursor = self.conn.execute("""
            SELECT M.fecha, M.km, M.descripcion, 
                T.nombre AS tipo_componente, 
                P.marca, P.modelo, P.tipo, 
                P.vida_util_km, P.vida_util_meses
            FROM Mantenimiento M
            JOIN Producto P ON M.id_producto = P.id_producto
            JOIN TipoComponente T ON P.id_tipo = T.id_tipo
            WHERE M.matricula = ?
            ORDER BY M.km
        """, (matricula,))

        fila = 2  # fila inicial después de encabezados
        for m in cursor.fetchall():
            # Procesar fecha de mantenimiento
            fecha_str = m["fecha"]
            fecha_dt = None
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    fecha_dt = datetime.strptime(fecha_str, fmt)
                    break
                except ValueError:
                    continue
            fecha_mostrar = fecha_dt.strftime("%d-%m-%Y") if fecha_dt else fecha_str

            # Calcular próximo cambio (km y fecha)
            prox_km = m["km"] + m["vida_util_km"] if m["vida_util_km"] else "-"
            prox_fecha = fecha_dt + timedelta(days=m["vida_util_meses"] * 30) if (fecha_dt and m["vida_util_meses"]) else None
            prox_fecha_str = prox_fecha.strftime("%d-%m-%Y") if prox_fecha else "-"

            # Datos para mostrar
            datos = [
                f"{m['tipo_componente']} - {m['marca']} {m['modelo']} ({m['tipo'] or '—'})",
                fecha_mostrar,
                m["km"],
                prox_km,
                prox_fecha_str,
                m["descripcion"] or "-"
            ]

            # Mostrar en interfaz
            for col, val in enumerate(datos):
                # Ajustar padding: más espacio a la izquierda para las primeras columnas
                if col == 0:  # Primera columna
                    padx = (15, 5)
                elif col == 1:  # Segunda columna
                    padx = (10, 5)
                else:  # Resto de columnas
                    padx = (8, 5)


                # Reducir tamaño de la columna de Descripción
                if col == 2:  # Suponiendo que la tercera columna es "Descripción"
                    font = ("Arial", 16)  # Fuente ligeramente más pequeña
                else:
                    font = ("Arial", 16)

                ctk.CTkLabel(self.frame_mantenimientos, text=str(val), font=font)\
                    .grid(row=fila, column=col, padx=padx, pady=2)

            fila += 1

        # Mostrar obligaciones del coche debajo de los mantenimientos
        self.mostrar_obligaciones_coche()


    def mostrar_obligaciones_coche(self):
        """Muestra las obligaciones del coche seleccionado en la pestaña Coches."""
        for widget in self.frame_obligaciones_coche.winfo_children():
            widget.destroy()

        matricula = self.coche_var.get().split(" ")[0] if self.coche_var.get() else None
        if not matricula:
            return

        # Título de sección
        ctk.CTkLabel(self.frame_obligaciones_coche, text="Obligaciones", font=("Arial", 20, "bold"))\
            .pack(pady=(5, 10))

        # Crear tabla (misma estructura visual que mantenimientos)
        tabla = ttk.Treeview(self.frame_obligaciones_coche, columns=("tipo", "descripcion", "inicio", "vencimiento"), show="headings", height=6)
        tabla.pack(padx=10, pady=5, fill="both", expand=True)

        # Cabeceras
        tabla.heading("tipo", text="Tipo")
        tabla.heading("descripcion", text="Descripción")
        tabla.heading("inicio", text="Inicio")
        tabla.heading("vencimiento", text="Vencimiento")

        tabla.column("tipo", width=80, anchor="center")
        tabla.column("descripcion", width=420, anchor="center")
        tabla.column("inicio", width=80, anchor="center")
        tabla.column("vencimiento", width=80, anchor="center")

        # Cargar datos
        cursor = self.conn.execute("""
            SELECT tipo, descripcion, fecha_inicio, fecha_vencimiento
            FROM Obligaciones
            WHERE matricula = ?
            ORDER BY fecha_vencimiento ASC
        """, (matricula,))

        for fila in cursor.fetchall():
            tabla.insert("", "end", values=(
                fila["tipo"],
                fila["descripcion"] or "-",
                fila["fecha_inicio"] or "-",
                fila["fecha_vencimiento"] or "-"
            ))

    def exportar_pdf(self):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from dateutil import parser
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        """Exporta a PDF el historial completo del vehículo, incluyendo mantenimientos, obligaciones, gastos y facturas."""

        def formatear_fecha(fecha_str):
            if not fecha_str:
                return "-"
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    fecha_dt = datetime.strptime(fecha_str, fmt)
                    return fecha_dt.strftime("%d-%m-%Y")
                except Exception:
                    continue
            return fecha_str

        coche_seleccionado = self.coche_var.get()
        if not coche_seleccionado:
            messagebox.showerror("Error", "Selecciona un coche primero.")
            return

        matricula = coche_seleccionado.split(" ")[0].strip()
        if not matricula:
            messagebox.showerror("Error", "No se pudo obtener la matrícula del coche.")
            return

        try:
            # --- Datos del coche ---
            cursor_coche = self.conn.execute(
                "SELECT marca, modelo, fecha_matriculacion, km_actuales FROM Coche WHERE matricula = ?",
                (matricula,)
            )
            coche_info = cursor_coche.fetchone()
            if not coche_info:
                messagebox.showerror("Error", f"No se encontró el coche con matrícula {matricula}.")
                return

            marca = coche_info["marca"]
            modelo = coche_info["modelo"]
            fecha_matriculacion = formatear_fecha(coche_info["fecha_matriculacion"])
            km_actuales = coche_info["km_actuales"] if coche_info["km_actuales"] is not None else 0

            pdf_name = f"{matricula.replace('/', '_').replace(' ', '_')}_informe_completo.pdf"
            doc = SimpleDocTemplate(pdf_name, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            centered = ParagraphStyle('centered', parent=styles['Normal'], alignment=TA_CENTER)

            # --- Encabezado principal ---
            title = Paragraph(f"<b>Informe del vehículo {matricula}</b>", styles['Title'])

            subtitle_text = (
                f"<b>Marca:</b> {marca} &nbsp;&nbsp; "
                f"<b>Modelo:</b> {modelo} &nbsp;&nbsp; "
                f"<b>Fecha matriculación:</b> {fecha_matriculacion} &nbsp;&nbsp;<br/> "
                f"<b>Kilómetros actuales:</b> {km_actuales} km"
            )

            subtitle = Paragraph(subtitle_text, centered)

            elements.extend([title, subtitle, Spacer(1, 16)])



            # MANTENIMIENTOS

            elements.append(Paragraph("<b>Mantenimientos</b>", styles['Heading2']))
            elements.append(Spacer(1, 8))

            cursor = self.conn.execute("""
                SELECT M.fecha, M.km, M.descripcion, 
                       T.nombre AS tipo, P.marca, P.modelo, P.tipo AS tipo_producto,
                       P.vida_util_km, P.vida_util_meses
                FROM Mantenimiento M
                JOIN Producto P ON M.id_producto = P.id_producto
                JOIN TipoComponente T ON P.id_tipo = T.id_tipo
                WHERE M.matricula = ?
                ORDER BY M.km
            """, (matricula,))
            mantenimientos = cursor.fetchall()

            if mantenimientos:
                data = [["Componente", "Fecha", "Km", "Próx. km", "Próx. fecha", "Descripción"]]
                for m in mantenimientos:
                    vida_km = m["vida_util_km"] or 0
                    vida_meses = m["vida_util_meses"] or 0
                    prox_km = f"{m['km'] + vida_km:.0f}" if vida_km else "-"
                    try:
                        fecha_dt = datetime.strptime(m["fecha"], "%Y-%m-%d")
                        prox_fecha = fecha_dt + timedelta(days=vida_meses * 30) if vida_meses else None
                        prox_fecha_str = prox_fecha.strftime("%d-%m-%Y") if prox_fecha else "-"
                    except Exception:
                        prox_fecha_str = "-"

                    data.append([
                        Paragraph(f"{m['tipo']} ({m['marca']} {m['modelo']} {m['tipo_producto']})", centered),
                        Paragraph(formatear_fecha(m["fecha"]), centered),
                        Paragraph(str(m["km"]), centered),
                        Paragraph(prox_km, centered),
                        Paragraph(prox_fecha_str, centered),
                        Paragraph(m["descripcion"] or "-", centered)
                    ])

                table = Table(data, repeatRows=1, colWidths=[140, 70, 55, 80, 80, 140])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey])
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No hay mantenimientos registrados.", styles['Normal']))


            # OBLIGACIONES

            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<b>Obligaciones</b>", styles['Heading2']))
            elements.append(Spacer(1, 8))

            cursor_oblig = self.conn.execute("""
                SELECT tipo, fecha_inicio, fecha_vencimiento, estado, descripcion
                FROM Obligaciones
                WHERE matricula = ?
                ORDER BY date(replace(fecha_vencimiento, '-', '/')) ASC
            """, (matricula,))
            obligaciones = cursor_oblig.fetchall()

            if obligaciones:
                data_obl = [["Tipo", "Inicio", "Vencimiento", "Estado", "Descripción"]]
                for o in obligaciones:
                    data_obl.append([
                        Paragraph(o["tipo"], centered),
                        Paragraph(formatear_fecha(o["fecha_inicio"]), centered),
                        Paragraph(formatear_fecha(o["fecha_vencimiento"]), centered),
                        Paragraph(o["estado"] or "-", centered),
                        Paragraph(o["descripcion"] or "-", centered)
                    ])

                table_obl = Table(data_obl, repeatRows=1, colWidths=[70, 70, 70, 60, 160])
                table_obl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey])
                ]))
                elements.append(table_obl)
            else:
                elements.append(Paragraph("No hay obligaciones registradas.", styles['Normal']))


            # GASTOS

            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<b>Gastos</b>", styles['Heading2']))
            elements.append(Spacer(1, 8))

            cursor_gastos = self.conn.execute("""
                SELECT G.fecha, G.categoria, G.concepto, G.importe, G.observaciones,
                       F.num_factura, F.fecha_emision, F.importe_total,
                       P.nombre AS proveedor
                FROM Gasto G
                LEFT JOIN Factura F ON G.id_factura = F.id_factura
                LEFT JOIN Proveedor P ON F.id_proveedor = P.id_proveedor
                WHERE G.matricula = ?
                ORDER BY date(replace(G.fecha, '-', '/')) DESC
            """, (matricula,))
            gastos = cursor_gastos.fetchall()

            total_gastos = 0

            if gastos:
                total_gastos = 0
                data_gastos = [["Fecha", "Categoría", "Concepto", "Importe (€)", "Factura / Proveedor", "Observaciones"]]
                for g in gastos:
                    total_gastos += g["importe"]
                    factura_info = "-"
                    if g["num_factura"]:
                        factura_info = f"{g['num_factura']} ({g['proveedor'] or '—'})"
                    data_gastos.append([
                        Paragraph(formatear_fecha(g["fecha"]), centered),
                        Paragraph(g["categoria"] or "-", centered),
                        Paragraph(g["concepto"], centered),
                        Paragraph(f"{g['importe']:.2f}", centered),
                        Paragraph(factura_info, centered),
                        Paragraph(g["observaciones"] or "-", centered)
                    ])

                table_gastos = Table(data_gastos, repeatRows=1, colWidths=[70, 70, 100, 70, 100, 90])
                table_gastos.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey])
                ]))
                elements.append(table_gastos)
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(f"<b>Total gastos:</b> {total_gastos:.2f} €", styles['Heading3']))
            else:
                elements.append(Paragraph("No hay gastos registrados.", styles['Normal']))


            # FACTURAS

            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<b>Facturas asociadas</b>", styles['Heading2']))
            elements.append(Spacer(1, 8))

            try:
                cursor_fact = self.conn.execute("""
                    SELECT 
                    f.num_factura,
                    p.nombre AS proveedor,
                    f.fecha_emision,
                    f.importe_total
                    FROM Factura f
                    JOIN Proveedor p ON f.id_proveedor = p.id_proveedor
                    WHERE TRIM(f.matricula) = ?
                    ORDER BY date(replace(f.fecha_emision, '-', '/')) DESC
                """, (matricula.strip(),))
                facturas = cursor_fact.fetchall()
            except Exception as e:
                print("Error al obtener facturas para el PDF:", e)
                facturas = []

            total_facturas = 0

            if facturas:
                total_facturas = 0.0
                data_facturas = [["Nº Factura", "Proveedor", "Fecha emisión", "Importe (€)"]]
                for f in facturas:
                    importe = float(f["importe_total"]) if f["importe_total"] else 0.0
                    total_facturas += importe
                    data_facturas.append([
                        Paragraph(f["num_factura"], centered),
                        Paragraph(f["proveedor"], centered),
                        Paragraph(formatear_fecha(f["fecha_emision"]), centered),
                        Paragraph(f"{importe:.2f}", centered)
                    ])

                tabla_facturas = Table(data_facturas, repeatRows=1, colWidths=[100, 150, 100, 80])
                tabla_facturas.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey])
                ]))
                elements.append(tabla_facturas)
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(f"<b>Total facturas:</b> {total_facturas:.2f} €", styles['Heading3']))
            else:
                elements.append(Paragraph("No hay facturas registradas.", styles['Normal']))


            # TOTAL GENERAL (Gastos + Facturas)

            total_general = total_gastos + total_facturas
            elements.append(Spacer(1, 15))
            elements.append(Paragraph(f"<b>Total Coste (Gastos + Facturas):</b> {total_general:.2f} €", styles['Heading2']))


            # Generar PDF

            doc.build(elements)
            messagebox.showinfo("PDF generado", f"✅ PDF '{pdf_name}' generado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")
            print("Error exportar_pdf:", e)


if __name__ == "__main__":
    inicializar_base_datos()
    root = ctk.CTk()
    app = MantenimientoApp(root)
    root.mainloop()