import tkinter as tk
from tkinter import messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
import asyncio
import threading
import socket
import json
from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription
from aiortc.contrib.media import MediaRelay

# Diccionario global para usuarios registrados
usuarios_registrados = {}  # {username: {'password': pass, 'ip': ip, 'port': port}}

# Variable global para el usuario actual
usuario_actual = None

# Servidor de señalización (corre en un hilo)
senalizacion_server = None
senalizacion_thread = None
senalizacion_conexiones = {}  # {username: socket}

# Función para iniciar servidor de señalización
def iniciar_senalizacion():
    global senalizacion_server, senalizacion_thread
    senalizacion_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    senalizacion_server.bind(('127.0.0.1', 9999))  # Puerto fijo para señalización
    senalizacion_server.listen(5)
    senalizacion_thread = threading.Thread(target=manejar_senalizacion, daemon=True)
    senalizacion_thread.start()

# Función para manejar señalización
def manejar_senalizacion():
    while True:
        client_socket, addr = senalizacion_server.accept()
        threading.Thread(target=manejar_cliente_senalizacion, args=(client_socket,), daemon=True).start()

def manejar_cliente_senalizacion(client_socket):
    username = client_socket.recv(1024).decode()
    senalizacion_conexiones[username] = client_socket
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            mensaje = json.loads(data.decode())
            destinatario = mensaje['to']
            if destinatario in senalizacion_conexiones:
                senalizacion_conexiones[destinatario].sendall(data)
        except:
            break
    del senalizacion_conexiones[username]
    client_socket.close()

# Función para mostrar vista previa de cámara
def mostrar_camara():
    if not usuario_actual:
        messagebox.showwarning("Advertencia", "Debes iniciar sesión.")
        return
    ventana_camara = tk.Toplevel(root)
    ventana_camara.title("Vista Previa de Cámara")
    etiqueta_video = tk.Label(ventana_camara)
    etiqueta_video.pack()
    cap = cv2.VideoCapture(0)
    def actualizar_frame():
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            etiqueta_video.img_tk = img_tk
            etiqueta_video.config(image=img_tk)
            etiqueta_video.after(10, actualizar_frame)
        else:
            messagebox.showerror("Error", "No se pudo acceder a la cámara.")
    actualizar_frame()

# Función para registrar usuario
def registrar_usuario():
    username = simpledialog.askstring("Registro", "Ingrese un nombre de usuario:")
    if not username:
        messagebox.showwarning("Advertencia", "El nombre de usuario no puede estar vacío.")
        return
    if username in usuarios_registrados:
        messagebox.showerror("Error", "El nombre de usuario ya existe.")
        return
    password = simpledialog.askstring("Registro", "Ingrese una contraseña:", show='*')
    if not password:
        messagebox.showwarning("Advertencia", "La contraseña no puede estar vacía.")
        return
    ip = simpledialog.askstring("Registro", "Ingrese su dirección IP:")
    if not ip:
        messagebox.showwarning("Advertencia", "La IP no puede estar vacía.")
        return
    port_str = simpledialog.askstring("Registro", "Ingrese un puerto:")
    if not port_str or not port_str.isdigit():
        messagebox.showwarning("Advertencia", "El puerto debe ser un número válido.")
        return
    port = int(port_str)
    usuarios_registrados[username] = {'password': password, 'ip': ip, 'port': port}
    messagebox.showinfo("Éxito", f"Usuario '{username}' registrado.")

# Función para iniciar sesión
def iniciar_sesion():
    global usuario_actual
    username = simpledialog.askstring("Iniciar Sesión", "Ingrese su nombre de usuario:")
    if not username:
        messagebox.showwarning("Advertencia", "El nombre de usuario no puede estar vacío.")
        return False
    if username not in usuarios_registrados:
        messagebox.showerror("Error", "Usuario no encontrado.")
        return False
    password = simpledialog.askstring("Iniciar Sesión", "Ingrese su contraseña:", show='*')
    if not password:
        messagebox.showwarning("Advertencia", "La contraseña no puede estar vacía.")
        return False
    if usuarios_registrados[username]['password'] == password:
        usuario_actual = username
        messagebox.showinfo("Éxito", f"Bienvenido, {username}!")
        conectar_senalizacion()
        return True
    else:
        messagebox.showerror("Error", "Contraseña incorrecta.")
        return False

# Función para conectar a señalización
def conectar_senalizacion():
    if not usuario_actual:
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9999))
        client_socket.sendall(usuario_actual.encode())
        senalizacion_conexiones[usuario_actual] = client_socket
    except:
        messagebox.showerror("Error", "No se pudo conectar al servidor de señalización.")

# Función para iniciar llamada
def iniciar_llamada():
    if not usuario_actual:
        messagebox.showwarning("Advertencia", "Debes iniciar sesión.")
        return
    if not usuarios_registrados:
        messagebox.showwarning("Advertencia", "No hay usuarios registrados.")
        return
    
    ventana_llamada = tk.Toplevel(root)
    ventana_llamada.title("Seleccionar Usuario")
    tk.Label(ventana_llamada, text="Seleccione un usuario:").pack(pady=10)
    lista_usuarios = tk.Listbox(ventana_llamada)
    for user in usuarios_registrados.keys():
        lista_usuarios.insert(tk.END, user)
    lista_usuarios.pack(pady=10)
    
    def llamar_seleccionado():
        seleccionado = lista_usuarios.get(tk.ACTIVE)
        if seleccionado and seleccionado != usuario_actual:
            asyncio.run(iniciar_llamada_webrtc(seleccionado))
            ventana_llamada.destroy()
        else:
            messagebox.showwarning("Advertencia", "Seleccione un usuario válido.")
    
    tk.Button(ventana_llamada, text="Llamar", command=llamar_seleccionado).pack(pady=10)

# Función asíncrona para iniciar llamada WebRTC
async def iniciar_llamada_webrtc(seleccionado):
    pc = RTCPeerConnection()
    # Agregar tracks de video/audio (necesitas instalar av para codecs)
    # Aquí un ejemplo básico; ajusta para tu cámara/micro
    # pc.addTrack(...)  # Agrega video track
    
    # Crear oferta
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    
    # Enviar oferta via señalización
    mensaje = json.dumps({'from': usuario_actual, 'to': seleccionado, 'type': 'offer', 'sdp': offer.sdp})
    if usuario_actual in senalizacion_conexiones:
        senalizacion_conexiones[usuario_actual].sendall(mensaje.encode())
    
    # Esperar respuesta (simplificado; en real, maneja eventos)
    # Para completitud, necesitarías manejar ice candidates, etc.
    messagebox.showinfo("Llamada", f"Llamada iniciada con {seleccionado}. (WebRTC en progreso - implementa manejo completo de eventos para video real)")

# Función para opciones
def opciones():
    if not usuario_actual:
        messagebox.showwarning("Advertencia", "Debes iniciar sesión.")
        return
    messagebox.showinfo("Opciones", "Configuración: Volumen al 50%.")

# Función para mostrar login
def mostrar_login():
    root.title("Iniciar Sesión")
    tk.Label(root, text="Nombre de Usuario:").grid(row=0, column=0, padx=10, pady=10)
    entry_username = tk.Entry(root)
    entry_username.grid(row=0, column=1, padx=10, pady=10)
    tk.Label(root, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10)
    entry_password = tk.Entry(root, show='*')
    entry_password.grid(row=1, column=1, padx=10, pady=10)
    
    def intentar_login():
        global usuario_actual
        username = entry_username.get()
        password = entry_password.get()
        if username in usuarios_registrados and usuarios_registrados[username]['password'] == password:
            usuario_actual = username
            messagebox.showinfo("Éxito", f"Bienvenido, {username}!")
            for widget in root.winfo_children():
                widget.destroy()
            configurar_app_principal()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
    
    tk.Button(root, text="Iniciar Sesión", command=intentar_login).grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(root, text="Registrarse", command=lambda: [registrar_usuario(), mostrar_login()]).grid(row=3, column=0, columnspan=2, pady=10)

# Función para configurar app principal
def configurar_app_principal():
    root.title("Aplicación de Llamadas")
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    menu_archivo = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Archivo", menu=menu_archivo)
    menu_archivo.add_command(label="Vista Previa de Cámara", command=mostrar_camara)
    menu_archivo.add_command(label="Iniciar Llamada", command=iniciar_llamada)
    menu_archivo.add_command(label="Opciones", command=opciones)
    menu_archivo.add_separator()
    menu_archivo.add_command(label="Salir", command=root.quit)
    menu_usuario = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Usuario", menu=menu_usuario)
    menu_usuario.add_command(label="Registrarse", command=registrar_usuario)
    menu_usuario.add_command(label="Iniciar Sesión", command=iniciar_sesion)

# Iniciar servidor de señalización al ejecutar
iniciar_senalizacion()

# Crear ventana principal
root = tk.Tk()
root.title("Aplicación de Llamadas")
mostrar_login()
root.mainloop()