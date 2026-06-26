import socket

# ifconfig | grep 192.168.1. - linux 
# sudo ufw allow 5000/tcp
# sudo ufw reload

HOST = '0.0.0.0'  # Escucha en todas las interfaces de red de la laptop
PORT = 5000

# Crear el socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Permitir reutilizar el puerto inmediatamente si el programa se reinicia
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"Servidor escuchando en el puerto {PORT}... Esperando datos de la placa.")

try:
    while True:
        # Aceptar la conexión de la placa
        client_socket, client_address = server_socket.accept()
        print(f"\nConexión establecida desde: {client_address}")
        
        # Recibir los datos
        datos = client_socket.recv(1024)
        if datos:
            print(f"Datos recibidos: {datos.decode('utf-8')}")
            
            # Enviar una respuesta de confirmación a la placa
            respuesta = "Datos recibidos correctamente en la laptop"
            client_socket.send(respuesta.encode('utf-8'))
        
        # Cerrar la conexión con este cliente
        client_socket.close()

except KeyboardInterrupt:
    print("\nApagando el servidor.")
finally:
    server_socket.close()