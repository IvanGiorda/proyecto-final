import tkinter as tk  # Para la interfaz gráfica
from tkinter import messagebox, simpledialog  # Para mostrar mensajes y diálogos simples
import cv2  # Para manejar la cámara
from PIL import Image, ImageTk  # Para convertir frames de OpenCV a Tkinter
import socket  # Para comunicación de red
import threading  # Para manejar hilos para recepción de video
import pickle  # Para serializar frames
import struct  # Para empaquetar datos

# Diccionario global para almacenar usuarios registrados (simulación de base de datos)
# Ahora incluye IP y puerto para llamadas reales
usuarios_registrados = {}  # {username: {'password': pass, 'ip': ip, 'port': port}}

# Variable global para el usuario actual logueado
usuario_actual = None

# Variable para el servidor de recepción
server_socket = None
server_thread = None

# Función para mostrar la vista previa de la cámara en una nueva ventana
def mostrar_camara():
    if not usuario_actual:
        messagebox.showwarning("Advertencia", "Debes iniciar sesión para usar esta función.")
        return
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

# Función para registrar un nuevo usuario
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
    ip = simpledialog.askstring("Registro", "Ingrese su dirección IP (ej. 127.0.0.1 para local):")
    if not ip:
        messagebox.showwarning("Advertencia", "La IP no puede estar vacía.")
        return
    port_str = simpledialog.askstring("Registro", "Ingrese un puerto (ej. 5000):")
    if not port_str or not port_str.isdigit():
        messagebox.showwarning("Advertencia", "El puerto debe ser un número válido.")
        return
    port = int(port_str)
    usuarios_registrados[username] = {'password': password, 'ip': ip, 'port': port}
    messagebox.showinfo("Éxito", f"Usuario '{username}' registrado exitosamente.")

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
        iniciar_servidor_recepcion()  # Iniciar servidor para recibir llamadas
        return True
    else:
        messagebox.showerror("Error", "Contraseña incorrecta.")
        return False

# Función para cerrar sesión
def cerrar_sesion():
    global usuario_actual, server_socket, server_thread
    if usuario_actual:
        usuario_actual = None
        if server_socket:
            server_socket.close()
            server_socket = None
        if server_thread and server_thread.is_alive():
            server_thread.join()
        messagebox.showinfo("Sesión Cerrada", "Has cerrado sesión.")
    else:
        messagebox.showwarning("Advertencia", "No hay sesión activa.")

# Función para iniciar el servidor de recepción
def iniciar_servidor_recepcion():
    global server_socket, server_thread
    if not usuario_actual:
        return
    port = usuarios_registrados[usuario_actual]['port']
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(('0.0.0.0', port))  # Escuchar en todas las interfaces
        server_socket.listen(1)
        server_thread = threading.Thread(target=escuchar_conexiones, daemon=True)
        server_thread.start()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar el servidor: {e}")

# Función para escuchar conexiones entrantes
def escuchar_conexiones():
    while usuario_actual and server_socket:
        try:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=manejar_llamada_entrante, args=(client_socket,), daemon=True).start()
        except:
            break

# Función para manejar una llamada entrante
def manejar_llamada_entrante(client_socket):
    # Crear ventana para la llamada entrante
    ventana_llamada_real = tk.Toplevel(root)
    ventana_llamada_real.title("Llamada Entrante")
    
    etiqueta_video_local = tk.Label(ventana_llamada_real, text="Tu video:")
    etiqueta_video_local.pack()
    etiqueta_video_remoto = tk.Label(ventana_llamada_real, text="Video del otro usuario:")
    etiqueta_video_remoto.pack()
    
    # Configurar captura de video local
    cap_local = cv2.VideoCapture(0)
    
    # Hilo para enviar video local
    def enviar_video():
        while True:
            ret, frame = cap_local.read()
            if ret:
                # Comprimir frame
                data = pickle.dumps(frame)
                message = struct.pack("Q", len(data)) + data
                try:
                    client_socket.sendall(message)
                except:
                    break
            else:
                break
        cap_local.release()
        client_socket.close()
    
    threading.Thread(target=enviar_video, daemon=True).start()
    
    # Hilo para recibir video remoto
    def recibir_video():
        data = b""
        payload_size = struct.calcsize("Q")
        while True:
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024)
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            
            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            
            frame = pickle.loads(frame_data)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            etiqueta_video_remoto.img_tk = img_tk
            etiqueta_video_remoto.config(image=img_tk)
    
    threading.Thread(target=recibir_video, daemon=True).start()
    
    # Mostrar video local en la ventana
    def actualizar_local():
        ret, frame = cap_local.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            etiqueta_video_local.img_tk = img_tk
            etiqueta_video_local.config(image=img_tk)
            etiqueta_video_local.after(10, actualizar_local)
    
    actualizar_local()

# Función para iniciar una llamada real a un usuario registrado
def iniciar_llamada():
    if not usuario_actual:
        messagebox.showwarning("Advertencia", "Debes iniciar sesión para usar esta función.")
        return
    if not usuarios_registrados:
        messagebox.showwarning("Advertencia", "No hay usuarios registrados para llamar.")
        return
    
    # Crear una ventana para seleccionar usuario
    ventana_llamada = tk.Toplevel(root)
    ventana_llamada.title("Seleccionar Usuario para Llamar")
    
    tk.Label(ventana_llamada, text="Seleccione un usuario registrado:").pack(pady=10)
    
    lista_usuarios = tk.Listbox(ventana_llamada)
    for user in usuarios_registrados.keys():
        lista_usuarios.insert(tk.END, user)
    lista_usuarios.pack(pady=10)
    
    def llamar_seleccionado():
        seleccionado = lista_usuarios.get(tk.ACTIVE)
        if seleccionado:
            # Obtener datos del usuario
            user_data = usuarios_registrados[seleccionado]
            ip = user_data['ip']
            port = user_data['port']
            
            # Iniciar la llamada real
            iniciar_llamada_real(ip, port)
            ventana_llamada.destroy()
        else:
            messagebox.showwarning("Advertencia", "Seleccione un usuario.")
    
    tk.Button(ventana_llamada, text="Llamar", command=llamar_seleccionado).pack(pady=10)

# Función para iniciar una llamada real (video streaming)
def iniciar_llamada_real(ip, port):
    # Crear ventana para la llamada
    ventana_llamada_real = tk.Toplevel(root)
    ventana_llamada_real.title("Llamada en Progreso")
    
    etiqueta_video_local = tk.Label(ventana_llamada_real, text="Tu video:")
    etiqueta_video_local.pack()
    etiqueta_video_remoto = tk.Label(ventana_llamada_real, text="Video del otro usuario:")
    etiqueta_video_remoto.pack()
    
    # Configurar socket para enviar
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip, port))
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo conectar: {e}")
        return
    
    # Configurar captura de video local
    cap_local = cv2.VideoCapture(0)
    
    # Hilo para enviar video local
    def enviar_video():
        while True:
            ret, frame = cap_local.read()
            if ret:
                # Comprimir frame
                data = pickle.dumps(frame)
                message = struct.pack("Q", len(data)) + data
                try:
                    client_socket.sendall(message)
                except:
                    break
            else:
                break
        cap_local.release()
        client_socket.close()
    
    threading.Thread(target=enviar_video, daemon=True).start()
    
    # Hilo para recibir video remoto
    def recibir_video():
        data = b""
        payload_size = struct.calcsize("Q")
        while True:
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024)
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            
            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            
            frame = pickle.loads(frame_data)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            etiqueta_video_remoto.img_tk = img_tk
            etiqueta_video_remoto.config(image=img_tk)
    
    threading.Thread(target=recibir_video, daemon=True).start()
    
    # Mostrar video local en la ventana
    def actualizar_local():
        ret, frame = cap_local.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            etiqueta_video_local.img_tk = img_tk
            etiqueta_video_local.config(image=img_tk)
            etiqueta_video_local.after(10, actualizar_local)
    
    actualizar_local()

# Función para opciones (simulada, por ejemplo, cambiar un mensaje)
def opciones():
    if not usuario_actual:
        messagebox.showwarning("Advertencia", "Debes iniciar sesión para usar esta función.")
        return
    messagebox.showinfo("Opciones", "Configuración: Volumen al 50% (simulado).")

# Función para mostrar la ventana de login al inicio
def mostrar_login():
    # Crear widgets de login en la ventana principal
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
            # Limpiar widgets de login y mostrar la app principal
            for widget in root.winfo_children():
                widget.destroy()
            configurar_app_principal()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
    
    tk.Button(root, text="Iniciar Sesión", command=intentar_login).grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(root, text="Registrarse", command=lambda: [registrar_usuario(), mostrar_login()]).grid(row=3, column=0, columnspan=2, pady=10)

# Función para configurar la app principal después del login
def configurar_app_principal():
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
    
    # Menú "Usuario" para registro y login
    menu_usuario = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Usuario", menu=menu_usuario)
    menu_usuario.add_command(label="Registrarse", command=registrar_usuario)
    menu_usuario.add_command(label="Iniciar Sesión", command=iniciar_sesion)
    menu_usuario.add_command(label="Cerrar Sesión", command=cerrar_sesion)

# Crear la ventana principal
root = tk.Tk()
root.title("Aplicación de Llamadas")

# Mostrar la ventana de login al inicio
mostrar_login()

# Iniciar el loop principal de la aplicación
root.mainloop()