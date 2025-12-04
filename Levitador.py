import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import time

# --- Matplotlib ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

serialInst = serial.Serial()

# Datos a graficar
tiempos = []
distancias = []
inicio_tiempo = time.time()

# ==============================
# FUNCIONES
# ==============================

def listar_puertos():
    ports = serial.tools.list_ports.comports()
    lista = [str(p).split(" ")[0] for p in ports]
    return lista


def conectar():
    com = comboPuertos.get()

    if com == "":
        estado.set("Selecciona un puerto.")
        return

    try:
        serialInst.port = com
        serialInst.baudrate = 9600
        serialInst.open()
        estado.set(f"Conectado a {com}")

        hilo = threading.Thread(target=leer_serial, daemon=True)
        hilo.start()

    except:
        estado.set("Error al abrir el puerto.")


def leer_serial():
    global tiempos, distancias

    while serialInst.is_open:
        try:
            if serialInst.in_waiting > 0:
                linea = serialInst.readline().decode("utf-8").strip()

                if "Posicion" in linea:
                    try:
                        valor = float(linea.split(" ")[1])
                        t = time.time() - inicio_tiempo
                        tiempos.append(t)
                        distancias.append(valor)
                        print(f"Posicion: {valor} cm | Tiempo: {t:.2f} s")
                        actualizar_grafica()
                        actualizar_info(valor)  # <-- ACTUALIZAR INFO
                    except:
                        pass

        except:
            break


# ==============================
# ACTUALIZAR INFORMACION
# ==============================
def actualizar_info(posicion_actual):
    sp = entry_sp.get().strip()
    
    # Actualizar posicion actual
    lbl_posicion_valor.config(text=f"{posicion_actual:.2f} cm", foreground="white")
    
    # Calcular y actualizar error
    if sp:
        try:
            setpoint = float(sp)
            error = setpoint - posicion_actual
            lbl_error_valor.config(text=f"{error:.2f} cm", foreground="white")
        except:
            lbl_error_valor.config(text="-- cm", foreground="white")
    else:
        lbl_error_valor.config(text="-- cm", foreground="white")


# ==============================
# ACTUALIZAR GRAFICA (ultimos 3 s)
# ==============================
def actualizar_grafica():
    ventana = 3.0  # 3 segundos visibles
    sp = entry_sp.get().strip()
    valorY = float(sp) if sp else None
    ax.clear()

    if len(tiempos) > 0:
        t_final = tiempos[-1]
        t_inicial = max(0, t_final - ventana)

        tiempos_filtrados = []
        dist_filtradas = []

        for t, d in zip(tiempos, distancias):
            if t >= t_inicial:
                tiempos_filtrados.append(t)
                dist_filtradas.append(d)

        ax.plot(tiempos_filtrados, dist_filtradas, linewidth=2)
        if valorY is not None:
            ax.axhline(y=valorY, color='r', linestyle='--', linewidth=2, label='Setpoint')
        ax.set_xlim(t_inicial, t_final)

    ax.set_ylim(0, 50)
    ax.set_title("Distancia vs Tiempo")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Distancia (cm)")
    ax.grid(True)
    ax.legend()

    canvas.draw()


# ==============================
# REINICIAR GRAFICA
# ==============================
def reiniciar_grafica():
    global tiempos, distancias, inicio_tiempo

    tiempos = []
    distancias = []
    inicio_tiempo = time.time()

    ax.clear()
    ax.set_ylim(0, 50)
    ax.set_title("Distancia vs Tiempo")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Distancia (cm)")
    ax.grid(True)

    canvas.draw()

    # Reiniciar valores de info
    lbl_posicion_valor.config(text="-- cm", foreground="white")
    lbl_error_valor.config(text="-- cm", foreground="white")

    estado.set("Grafica reiniciada")


# ==============================
# ENVIAR PARAMETROS PID
# ==============================
def enviar_parametros():
    if not serialInst.is_open:
        estado.set("Conectate primero al puerto.")
        return

    sp = entry_sp.get().strip()
    kp = entry_kp.get().strip()
    ki = entry_ki.get().strip()
    kd = entry_kd.get().strip()

    try:
        sp_original = float(sp)
        sp_modificado = sp_original + 20
        
        comando = f"{sp_modificado},{kp},{ki},{kd}\n"
        
        serialInst.write(comando.encode())
        estado.set(f"Enviado: {comando.strip()}")
        print(f"\n--- Parametros PID enviados ---")
        print(f"Setpoint ingresado: {sp_original} cm")
        print(f"Setpoint enviado: {sp_modificado} cm (+ 20)")
        print(f"Kp: {kp}")
        print(f"Ki: {ki}")
        print(f"Kd: {kd}")
        print(f"-------------------------------\n")

        reiniciar_grafica()

    except ValueError:
        estado.set("Error: Ingresa valores numericos validos.")
    except:
        estado.set("Error al enviar parametros.")


# ==============================
# GUI
# ==============================

root = tk.Tk()
root.title("Monitor de Distancia - Arduino")
root.geometry("900x700")

estado = tk.StringVar(value="Selecciona un puerto y conecta")

# ==============================
# FRAME PRINCIPAL CON DOS COLUMNAS
# ==============================
frame_principal = ttk.Frame(root)
frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# --- COLUMNA IZQUIERDA: Panel de informacion ---
frame_izquierdo = ttk.LabelFrame(frame_principal, text="Informacion en Tiempo Real", padding=15)
frame_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

# Posicion actual
ttk.Label(frame_izquierdo, text="Posicion Actual:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 5))
lbl_posicion_valor = ttk.Label(frame_izquierdo, text="-- cm", font=("Arial", 20), foreground="white")
lbl_posicion_valor.pack(anchor="w", pady=(0, 20))

# Error
ttk.Label(frame_izquierdo, text="Error (SP - Actual):", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 5))
lbl_error_valor = ttk.Label(frame_izquierdo, text="-- cm", font=("Arial", 20), foreground="white")
lbl_error_valor.pack(anchor="w", pady=(0, 20))

# Separador
ttk.Separator(frame_izquierdo, orient='horizontal').pack(fill='x', pady=10)

# Setpoint de referencia
ttk.Label(frame_izquierdo, text="Setpoint de Referencia:", font=("Arial", 11)).pack(anchor="w", pady=(0, 5))
lbl_sp_ref = ttk.Label(frame_izquierdo, text="--", font=("Arial", 20, "bold"), foreground="white")
lbl_sp_ref.pack(anchor="w")


# --- COLUMNA DERECHA: Controles y grafica ---
frame_derecho = ttk.Frame(frame_principal)
frame_derecho.grid(row=0, column=1, sticky="nsew")

# Configurar pesos de columnas
frame_principal.columnconfigure(0, weight=1)
frame_principal.columnconfigure(1, weight=3)
frame_principal.rowconfigure(0, weight=1)

# --- Selector de puerto ---
frame_puerto = ttk.Frame(frame_derecho)
frame_puerto.pack(pady=5)

ttk.Label(frame_puerto, text="Puerto COM:").pack()

# Frame para el selector y boton de refresh
frame_selector = ttk.Frame(frame_puerto)
frame_selector.pack()

comboPuertos = tk.StringVar()
lista = listar_puertos()
menu = ttk.OptionMenu(frame_selector, comboPuertos, lista[0] if lista else "", *lista)
menu.pack(side=tk.LEFT, padx=(0, 5))

# Funcion para refrescar la lista de puertos
def refrescar_puertos():
    lista = listar_puertos()
    menu['menu'].delete(0, 'end')
    
    if lista:
        comboPuertos.set(lista[0])
        for puerto in lista:
            menu['menu'].add_command(label=puerto, command=tk._setit(comboPuertos, puerto))
        estado.set(f"Lista actualizada: {len(lista)} puerto(s) encontrado(s)")
    else:
        comboPuertos.set("")
        estado.set("No se encontraron puertos COM")

ttk.Button(frame_selector, text="Refrescar", command=refrescar_puertos).pack(side=tk.LEFT)

ttk.Button(frame_puerto, text="Conectar", command=conectar).pack(pady=5)

# --- Entradas PID ---
frm_pid = ttk.Frame(frame_derecho)
frm_pid.pack(pady=10)

ttk.Label(frm_pid, text="Setpoint (SP):").grid(row=0, column=0, padx=5)
entry_sp = ttk.Entry(frm_pid, width=10)
entry_sp.grid(row=0, column=1)

# Actualizar label del setpoint cuando cambie
def actualizar_sp_label(*args):
    sp = entry_sp.get().strip()
    if sp:
        try:
            lbl_sp_ref.config(text=f"{float(sp):.2f} cm")
        except:
            lbl_sp_ref.config(text="--")
    else:
        lbl_sp_ref.config(text="--")

entry_sp.bind('<KeyRelease>', actualizar_sp_label)

ttk.Label(frm_pid, text="Kp:").grid(row=1, column=0, padx=5)
entry_kp = ttk.Entry(frm_pid, width=10)
entry_kp.grid(row=1, column=1)

ttk.Label(frm_pid, text="Ki:").grid(row=2, column=0, padx=5)
entry_ki = ttk.Entry(frm_pid, width=10)
entry_ki.grid(row=2, column=1)

ttk.Label(frm_pid, text="Kd:").grid(row=3, column=0, padx=5)
entry_kd = ttk.Entry(frm_pid, width=10)
entry_kd.grid(row=3, column=1)

ttk.Button(frame_derecho, text="Enviar parametros PID", command=enviar_parametros).pack(pady=10)
ttk.Button(frame_derecho, text="Reiniciar grafica", command=reiniciar_grafica).pack(pady=5)

# --- Grafica ---
fig = plt.Figure(figsize=(6, 4), dpi=100)
ax = fig.add_subplot(111)
ax.set_title("Distancia vs Tiempo")
ax.set_ylim(0, 50)

canvas = FigureCanvasTkAgg(fig, master=frame_derecho)
canvas.get_tk_widget().pack()

# --- Estado ---
ttk.Label(root, textvariable=estado).pack(pady=5)

root.mainloop()