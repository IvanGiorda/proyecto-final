import tkinter as tk  # Para la interfaz gráfica
from tkinter import messagebox  # Para mostrar mensajes
import cv2  # Para manejar la cámara
from PIL import Image, ImageTk  # Para convertir frames de OpenCV a Tkinter

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
            messagebox.showerror("Error", "No se pudo acceder a la cámara.")
    
    actualizar_frame()  # Inicia el loop

# Función para simular el inicio de una llamada
def iniciar_llamada():
    messagebox.showinfo("Llamada", "Llamada iniciada con éxito! (Simulación)")

# Función para opciones (simulada, por ejemplo, cambiar un mensaje)
def opciones():
    messagebox.showinfo("Opciones", "Configuración: Volumen al 50% (simulado).")

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
menu_archivo.add_command(label="Opciones", command=opciones)
menu_archivo.add_separator()
menu_archivo.add_command(label="Salir", command=root.quit)

# Iniciar el loop principal de la aplicación
root.mainloop()