import tkinter as tk  # Para la interfaz gráfica
from tkinter import messagebox, simpledialog, Toplevel  # Para mostrar mensajes y diálogos
import cv2  # Para manejar la cámara
from PIL import Image, ImageTk  # Para convertir frames de OpenCV a Tkinter
import sqlite3  # Para base de datos real
import sys  # Para detectar el sistema operativo

# Intentar importar pycaw para control de volumen en Windows
try:
    if sys.platform == "win32":
        from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume  # Para controlar volumen en Windows
    else:
        raise ImportError("pycaw no es compatible con este SO.")
except ImportError:
    print("Advertencia: pycaw no está instalado. El control de volumen no funcionará en Windows.")
    AudioUtilities = None  # Placeholder

# Conectar a la base de datos SQLite (crea una si no existe)
conn = sqlite3.connect('usuarios.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS usuarios
             (nombre TEXT, email TEXT)''')  # Tabla simple para usuarios
conn.commit()

# Función para mostrar la vista previa de la cámara en una nueva ventana (simula una llamada)
def mostrar_camara(usuario_destino):
    ventana_camara = tk.Toplevel(root)  # Crea una nueva ventana
    ventana_camara.title(f"Llamada con {usuario_destino}")
    
    etiqueta_video = tk.Label(ventana_camara)  # Etiqueta para mostrar el video
    etiqueta_video.pack()
    
    cap = cv2.VideoCapture(0)  # Accede a la cámara
    
    def actualizar_frame():
        ret, frame = cap.read()  # Lee un frame
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            etiqueta_video.img_tk = img_tk
            etiqueta_video.config(image=img_tk)
            etiqueta_video.after(10, actualizar_frame)
        else:
            messagebox.showerror("Error", "No se pudo acceder a la cámara.")
    
    def cerrar_ventana():
        cap.release()
        ventana_camara.destroy()
    
    ventana_camara.protocol("WM_DELETE_WINDOW", cerrar_ventana)
    actualizar_frame()

# Función para iniciar una llamada real (ahora usa la cámara con el usuario seleccionado)
def iniciar_llamada():
    # Obtener usuarios de la base de datos
    c.execute("SELECT nombre FROM usuarios")
    usuarios = [row[0] for row in c.fetchall()]
    
    if not usuarios:
        messagebox.showwarning("Advertencia", "No hay usuarios registrados. Registra uno primero.")
        return
    
    usuario_seleccionado = simpledialog.askstring("Seleccionar Usuario", "Ingrese el nombre del usuario para llamar:")
    
    if usuario_seleccionado in usuarios:
        mostrar_camara(usuario_seleccionado)  # Inicia la cámara como "llamada"
    else:
        messagebox.showerror("Error", "Usuario no encontrado.")

# Función para registrar un usuario (ahora guarda en SQLite)
def registrar_usuario():
    ventana_registro = Toplevel(root)
    ventana_registro.title("Registrar Usuario")
    
    tk.Label(ventana_registro, text="Nombre:").pack()
    entry_nombre = tk.Entry(ventana_registro)
    entry_nombre.pack()
    
    tk.Label(ventana_registro, text="Email:").pack()
    entry_email = tk.Entry(ventana_registro)
    entry_email.pack()
    
    def guardar_usuario():
        nombre = entry_nombre.get()
        email = entry_email.get()
        
        if nombre and email:
            c.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (nombre, email))
            conn.commit()
            messagebox.showinfo("Éxito", f"Usuario {nombre} registrado con éxito!")
            ventana_registro.destroy()
        else:
            messagebox.showerror("Error", "Por favor, ingresa nombre y email.")
    
    tk.Button(ventana_registro, text="Guardar", command=guardar_usuario).pack()

# Función para subir el volumen (real para Windows)
def subir_volumen():
    if sys.platform == "win32" and AudioUtilities:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            if volume.GetMasterVolume() is not None:
                currentVolume = volume.GetMasterVolume() * 100  # Obtener volumen actual
                newVolume = min(currentVolume + 10, 100)  # Incrementar en 10%
                volume.SetMasterVolume(newVolume / 100)  # Establecer nuevo volumen
                messagebox.showinfo("Volumen", f"Volumen subido a {newVolume}%")
        return
    messagebox.showinfo("Volumen", "Control de volumen no disponible en este sistema.")

# Función para bajar el volumen (real para Windows)
def bajar_volumen():
    if sys.platform == "win32" and AudioUtilities:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            if volume.GetMasterVolume() is not None:
                currentVolume = volume.GetMasterVolume() * 100
                newVolume = max(currentVolume - 10, 0)  # Decrementar en 10%
                volume.SetMasterVolume(newVolume / 100)
                messagebox.showinfo("Volumen", f"Volumen bajado a {newVolume}%")
        return
    messagebox.showinfo("Volumen", "Control de volumen no disponible en este sistema.")

# Crear la ventana principal
root = tk.Tk()
root.title("Aplicación de Llamadas")

# Crear el menú principal
menubar = tk.Menu(root)
root.config(menu=menubar)

# Menú "Archivo"
menu_archivo = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Archivo", menu=menu_archivo)
menu_archivo.add_command(label="Vista Previa de Cámara", command=mostrar_camara)
menu_archivo.add_command(label="Iniciar Llamada", command=iniciar_llamada)
menu_archivo.add_command(label="Opciones", command=lambda: messagebox.showinfo("Opciones", "Configuración actualizada."))
menu_archivo.add_separator()
menu_archivo.add_command(label="Salir", command=root.quit)

# Menú "Usuarios"
menu_usuarios = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Usuarios", menu=menu_usuarios)
menu_usuarios.add_command(label="Registrar Usuario", command=registrar_usuario)

# Menú "Opciones" con subopciones
menu_opciones = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Opciones", menu=menu_opciones)
menu_opciones.add_command(label="Subir Volumen", command=subir_volumen)
menu_opciones.add_command(label="Bajar Volumen", command=bajar_volumen)

root.mainloop()

# Cierra la conexión a la base de datos al final (aunque es mejor manejarlo con un contexto)
conn.close()