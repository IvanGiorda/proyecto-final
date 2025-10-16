import tkinter as tk  # Para la interfaz gráfica
from tkinter import messagebox, simpledialog, Toplevel  # Para mostrar mensajes y diálogos
import cv2  # Para manejar la cámara
from PIL import Image, ImageTk  # Para convertir frames de OpenCV a Tkinter

# Variables globales para usuarios y volumen
usuarios_registrados = []  # Lista para almacenar usuarios (ej: [{'nombre': 'Juan', 'email': 'juan@example.com'}])
volumen_actual = 50  # Nivel inicial de volumen (de 0 a 100)

# Función para mostrar la vista previa de la cámara en una nueva ventana
def mostrar_camara():
    ventana_camara = tk.Toplevel(root)  # Crea una nueva ventana
    ventana_camara.title("Vista Previa de Cámara")
    
    etiqueta_video = tk.Label(ventana_camara)  # Etiqueta para mostrar el video
    etiqueta_video.pack()
    
    cap = cv2.VideoCapture(0)  # Accede a la cámara (0 es la cámara predeterminada)
    
    def actualizar_frame():
        ret, frame = cap.read()  # Lee un frame de la cámara
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convierte a formato RGB
            img = Image.fromarray(frame)  # Convierte a imagen PIL
            img_tk = ImageTk.PhotoImage(image=img)  # Convierte a formato Tkinter
            etiqueta_video.img_tk = img_tk  # Mantiene una referencia
            etiqueta_video.config(image=img_tk)  # Actualiza la etiqueta
            etiqueta_video.after(10, actualizar_frame)  # Llama a la función cada 10 ms
        else:
            messagebox.showerror("Error", "No se pudo acceder a la cámara o leer un frame.")
    
    # Función para cerrar la ventana y liberar la cámara
    def cerrar_ventana():
        cap.release()  # Libera la cámara
        ventana_camara.destroy()  # Cierra la ventana
    
    ventana_camara.protocol("WM_DELETE_WINDOW", cerrar_ventana)  # Asocia el cierre de ventana a la función
    
    actualizar_frame()  # Inicia el loop

# Función para simular el inicio de una llamada (ahora incluye selección de usuario)
def iniciar_llamada():
    if not usuarios_registrados:
        messagebox.showwarning("Advertencia", "No hay usuarios registrados. Registra uno primero.")
        return
    
    # Muestra una lista de usuarios para seleccionar (simulado)
    usuario_seleccionado = simpledialog.askstring("Seleccionar Usuario", "Ingrese el nombre del usuario para llamar:")
    
    if usuario_seleccionado in [usuario['nombre'] for usuario in usuarios_registrados]:
        messagebox.showinfo("Llamada", f"Llamada iniciada con {usuario_seleccionado}! (Simulación)")
    else:
        messagebox.showerror("Error", "Usuario no encontrado.")

# Función para registrar un usuario
def registrar_usuario():
    ventana_registro = Toplevel(root)  # Crea una nueva ventana para registro
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
        
        if nombre and email:  # Verifica que no estén vacíos
            usuarios_registrados.append({'nombre': nombre, 'email': email})
            messagebox.showinfo("Éxito", f"Usuario {nombre} registrado con éxito!")
            ventana_registro.destroy()  # Cierra la ventana
        else:
            messagebox.showerror("Error", "Por favor, ingresa nombre y email.")
    
    tk.Button(ventana_registro, text="Guardar", command=guardar_usuario).pack()

# Función para subir el volumen
def subir_volumen():
    global volumen_actual
    if volumen_actual < 100:
        volumen_actual += 10  # Incrementa en 10 unidades
        messagebox.showinfo("Volumen", f"Volumen subido a {volumen_actual}%")
    else:
        messagebox.showinfo("Volumen", "Volumen ya está al máximo (100%).")

# Función para bajar el volumen
def bajar_volumen():
    global volumen_actual
    if volumen_actual > 0:
        volumen_actual -= 10  # Decrementa en 10 unidades
        messagebox.showinfo("Volumen", f"Volumen bajado a {volumen_actual}%")
    else:
        messagebox.showinfo("Volumen", "Volumen ya está al mínimo (0%).")

# Crear la ventana principal
root = tk.Tk()
root.title("Aplicación de Llamadas")

# Crear el menú principal
menubar = tk.Menu(root)
root.config(menu=menubar)

# Menú "Archivo" con las opciones
menu_archivo = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Archivo", menu=menu_archivo)
menu_archivo.add_command(label="Vista Previa de Cámara", command=mostrar_camara)
menu_archivo.add_command(label="Iniciar Llamada", command=iniciar_llamada)
menu_archivo.add_command(label="Opciones", command=lambda: messagebox.showinfo("Opciones", f"Configuración: Volumen al {volumen_actual}% (simulado)."))
menu_archivo.add_separator()
menu_archivo.add_command(label="Salir", command=root.quit)

# Menú "Usuarios" para registrar
menu_usuarios = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Usuarios", menu=menu_usuarios)
menu_usuarios.add_command(label="Registrar Usuario", command=registrar_usuario)

# Menú "Opciones" con subopciones para volumen (agregado como submenú)
menu_opciones = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Opciones", menu=menu_opciones)
menu_opciones.add_command(label="Subir Volumen", command=subir_volumen)
menu_opciones.add_command(label="Bajar Volumen", command=bajar_volumen)

# Iniciar el loop principal de la aplicación
root.mainloop()