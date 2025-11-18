"""
Sistema de correo OOP (version final 2.0.1 (? mas simple y organizado)
- Clases: Usuario, Mensaje, Carpeta, ServidorCorreo, ServidorCorreoAvanzado
- Encapsulamiento con propiedades
- Enviar/recibir/listar mensajes
- Carpetas y subcarpetas (arbol recursivo)
- Mover mensajes y busquedas recursivas
- Filtros automaticos (dict)
- Cola de prioridad para urgentes (heapq)
- Red de servidores (grafo) y BFS (Busqueda de anchura o como se dice en ingles (Breadth-First Search)
- Menu
"""

from __future__ import annotations
from typing import List, Optional
from datetime import datetime
import itertools
import heapq
from collections import deque

# contador de ids
_id_counter = itertools.count(1)



#Mensajes

class Mensaje:
    """mensaje simple de correo"""

    def __init__(self, remitente: str, destinatario: str, asunto: str, cuerpo: str):
        self._id = next(_id_counter)
        self._remitente = remitente
        self._destinatario = destinatario
        self._asunto = asunto
        self._cuerpo = cuerpo
        self._timestamp = datetime.now()
        self._leido = False

    @property
    def id(self): return self._id

    @property
    def remitente(self): return self._remitente

    @property
    def destinatario(self): return self._destinatario

    @property
    def asunto(self): return self._asunto

    @property
    def cuerpo(self): return self._cuerpo

    @property
    def timestamp(self): return self._timestamp

    @property
    def leido(self): return self._leido

    def marcar_leido(self):
        self._leido = True

    def __repr__(self):
        return f"Mensaje(id={self._id}, from={self._remitente}, subj={self._asunto})"


#Carpetas

class Carpeta:
    def __init__(self, nombre: str, padre: Optional["Carpeta"] = None):
        self._nombre = nombre
        self._padre = padre
        self._subcarpetas: List[Carpeta] = []
        self._mensajes: List[Mensaje] = []

    @property
    def nombre(self): return self._nombre

    @property
    def padre(self): return self._padre

    @property
    def subcarpetas(self): return list(self._subcarpetas)

    @property
    def mensajes(self): return list(self._mensajes)

    def crear_subcarpeta(self, nombre: str):
        nueva = Carpeta(nombre, self)
        self._subcarpetas.append(nueva)
        return nueva

    def agregar_mensaje(self, mensaje: Mensaje):
        self._mensajes.append(mensaje)

    def eliminar_mensaje_por_id(self, mensaje_id: int):
        for i, m in enumerate(self._mensajes):
            if m.id == mensaje_id:
                return self._mensajes.pop(i)
        return None

    def buscar_mensajes_por_asunto(self, texto: str):

        texto = texto.lower()
        encontrados = [m for m in self._mensajes if texto in m.asunto.lower()]
        for sub in self._subcarpetas:
            encontrados.extend(sub.buscar_mensajes_por_asunto(texto))
        return encontrados

    def buscar_mensajes_por_remitente(self, remit: str):
        remit = remit.lower()
        encontrados = [m for m in self._mensajes if remit == m.remitente.lower()]
        for sub in self._subcarpetas:
            encontrados.extend(sub.buscar_mensajes_por_remitente(remit))
        return encontrados

    def encontrar_subcarpeta_por_ruta(self, ruta: List[str]):
        if not ruta:
            return self
        nombre = ruta[0]
        for sub in self._subcarpetas:
            if sub.nombre == nombre:
                return sub.encontrar_subcarpeta_por_ruta(ruta[1:])
        return None

    def mover_mensaje_a(self, mensaje_id: int, destino: "Carpeta"):
        mensaje = self.eliminar_mensaje_por_id(mensaje_id)
        if mensaje:
            destino.agregar_mensaje(mensaje)
            return True
        for sub in self._subcarpetas:
            if sub.mover_mensaje_a(mensaje_id, destino):
                return True
        return False

    def listar_estructura(self, nivel=0):
        print("  " * nivel + f"- {self._nombre} ({len(self._mensajes)} mensajes)")
        for m in self._mensajes:
            print("  " * (nivel + 1) + f"* {m}")
        for sub in self._subcarpetas:
            sub.listar_estructura(nivel + 1)



# Clase de usuario

class Usuario:
    def __init__(self, nombre: str, email: str):
        self._nombre = nombre
        self._email = email

        self._root = Carpeta("root")
        self._inbox = self._root.crear_subcarpeta("inbox")
        self._sent = self._root.crear_subcarpeta("sent")
        self._trash = self._root.crear_subcarpeta("trash")

    @property
    def nombre(self): return self._nombre

    @property
    def email(self): return self._email

    @property
    def root(self): return self._root

    @property
    def inbox(self): return self._inbox

    @property
    def sent(self): return self._sent

    @property
    def trash(self): return self._trash

    def recibir_mensaje(self, mensaje: Mensaje, carpeta_destino: Optional[Carpeta] = None):
        if carpeta_destino is None:
            carpeta_destino = self._inbox
        carpeta_destino.agregar_mensaje(mensaje)

    def mover_mensaje(self, mensaje_id: int, ruta_destino: List[str]):
        destino = self._root.encontrar_subcarpeta_por_ruta(ruta_destino)
        if not destino:
            return False
        return self._root.mover_mensaje_a(mensaje_id, destino)

    def listar_carpetas(self):
        print(f"Carpetas de {self._email}:")
        self._root.listar_estructura()



# Clase de servidor comun

class ServidorCorreo:
    def __init__(self):
        self._usuarios: dict[str, Usuario] = {}

    def registrar_usuario(self, usuario: Usuario):
        self._usuarios[usuario.email] = usuario

    def enviar(self, remitente: str, destinatario: str, asunto: str, cuerpo: str):
        if remitente not in self._usuarios:
            print("Remitente no registrado")
            return None
        if destinatario not in self._usuarios:
            print("Destinatario no registrado")
            return None

        mensaje = Mensaje(remitente, destinatario, asunto, cuerpo)
        self._usuarios[destinatario].recibir_mensaje(mensaje)
        self._usuarios[remitente].sent.agregar_mensaje(mensaje)
        return mensaje

    def listar_usuarios(self):
        print("Usuarios:")
        for u in self._usuarios.values():
            print(f"- {u.nombre} ({u.email})")



# Clase del servidor correo avanzado

class ServidorCorreoAvanzado(ServidorCorreo):
    def __init__(self, nombre):
        super().__init__()
        self._nombre = nombre
        self._filtros: dict[str, str] = {}
        self._cola_prioridad: list[tuple[int, Mensaje]] = []
        self._conexiones: dict[str, list[str]] = {}

    # filtro
    def agregar_filtro(self, clave: str, carpeta: str):
        self._filtros[clave.lower()] = carpeta.lower()

    def aplicar_filtros(self, usuario: Usuario, mensaje: Mensaje):
        for palabra, carpeta in self._filtros.items():
            if palabra in mensaje.asunto.lower() or palabra in mensaje.cuerpo.lower():
                destino = usuario.root.encontrar_subcarpeta_por_ruta([carpeta])
                if destino:
                    ok = usuario.mover_mensaje(mensaje.id, [carpeta])
                    if ok:
                        print(f"Filtro '{palabra}' aplicado: movio a '{carpeta}'")
                    else:
                        print("No se pudo mover el mensaje")
                else:
                    print(f"La carpeta '{carpeta}' no existe. El filtro no se aplico.")
                return
        print("No se aplico ningun filtro")

    # Mensajes urgentes
    def agregar_mensaje_urgente(self, mensaje: Mensaje, prioridad: int):
        heapq.heappush(self._cola_prioridad, (prioridad, mensaje))
        print(f"Mensaje urgente agregado con prioridad {prioridad}")

    def procesar_mensajes_urgentes(self):
        print("Procesando cola de urgentes...")
        while self._cola_prioridad:
            prioridad, mensaje = heapq.heappop(self._cola_prioridad)
            print(f"URGENTE (p={prioridad}): {mensaje.asunto}")

    # Red de servidores (grafo)
    def conectar_servidor(self, otro: "ServidorCorreoAvanzado"):
        self._conexiones.setdefault(self._nombre, [])
        self._conexiones.setdefault(otro._nombre, [])

        if otro._nombre not in self._conexiones[self._nombre]:
            self._conexiones[self._nombre].append(otro._nombre)
        if self._nombre not in self._conexiones[otro._nombre]:
            self._conexiones[otro._nombre].append(self._nombre)

        print(f"Conectado: {self._nombre} <-> {otro._nombre}")

    def mostrar_conexiones(self):
        if not self._conexiones:
            print("(sin conexiones registradas)")
        for serv, vecinos in self._conexiones.items():
            print(f"{serv}: {vecinos}")

    def enviar_mensaje_red(self, origen: str, destino: str):
        if origen not in self._conexiones or destino not in self._conexiones:
            print("Servidor no encontrado en la red")
            return

        print(f"Iniciando BFS desde {origen} hacia {destino}")
        visitados = set()
        cola = deque([origen])

        while cola:
            actual = cola.popleft()
            if actual == destino:
                print(f"Mensaje entregado correctamente de {origen} a {destino}")
                return
            if actual in visitados:
                continue
            visitados.add(actual)
            for vecino in self._conexiones.get(actual, []):
                if vecino not in visitados:
                    cola.append(vecino)

        print("No se pudo entregar el mensaje en la red")



# menu interactivo

def menu():
    print("\n============================")
    print("      SISTEMA DE CORREO  ")
    print("============================")
    print("1. Registrar usuario")
    print("2. Enviar mensaje")
    print("3. Listar usuarios")
    print("4. Ver carpetas de un usuario")
    print("5. Agregar filtro automatico")
    print("6. Marcar mensaje urgente")
    print("7. Procesar mensajes urgentes")
    print("8. Conectar servidores")
    print("9. Mostrar red de servidores")
    print("10. Enviar mensaje a traves de la red (BFS)")
    print("0. Salir")
    return input("Seleccione una opcion: ")


def iniciar_programa():
    servidor = ServidorCorreoAvanzado("ServidorPrincipal")
    servidores_red = {"ServidorPrincipal": servidor}

    print("Sistema iniciado.\n")

    while True:
        opcion = menu()

        # 1. Registrar usuario
        if opcion == "1":
            nombre = input("Nombre del usuario: ")
            email = input("Email del usuario: ")
            user = Usuario(nombre, email)
            servidor.registrar_usuario(user)
            print("Usuario registrado correctamente.")

        # 2. Enviar mensaje
        elif opcion == "2":
            rem = input("Remitente: ")
            dest = input("Destinatario: ")
            asunto = input("Asunto: ")
            cuerpo = input("Cuerpo del mensaje: ")
            mensaje = servidor.enviar(rem, dest, asunto, cuerpo)
            if mensaje and dest in servidor._usuarios:
                print("Mensaje enviado.")
                servidor.aplicar_filtros(servidor._usuarios[dest], mensaje)

        # 3. Listar usuarios
        elif opcion == "3":
            servidor.listar_usuarios()

        # 4. Ver carpetas
        elif opcion == "4":
            email = input("Email del usuario: ")
            if email in servidor._usuarios:
                servidor._usuarios[email].listar_carpetas()
            else:
                print("Usuario no encontrado.")

        # 5. Agregar filtro
        elif opcion == "5":
            clave = input("Palabra clave: ")
            carpeta = input("Carpeta destino (por ej: inbox, sent, trash o alguna creada): ")
            servidor.agregar_filtro(clave, carpeta)
            print("Filtro agregado.")

        # 6. Marcar mensaje urgente (busca en todo el arbol)
        elif opcion == "6":
            email = input("Email del usuario: ")
            if email not in servidor._usuarios:
                print("Usuario no existe.")
                continue
            usuario = servidor._usuarios[email]
            try:
                msg_id = int(input("ID del mensaje: "))
                prioridad = int(input("Prioridad (1 = alta): "))
            except ValueError:
                print("IDs o prioridad invalidos.")
                continue

            todos = usuario.root.buscar_mensajes_por_asunto("")  # trae todos
            encontrado = next((m for m in todos if m.id == msg_id), None)
            if encontrado:
                servidor.agregar_mensaje_urgente(encontrado, prioridad)
                print("Mensaje marcado como urgente.")
            else:
                print("Mensaje no encontrado.")

        # 7. Procesar mensajes urgentes
        elif opcion == "7":
            servidor.procesar_mensajes_urgentes()

        # 8. Conectar servidores
        elif opcion == "8":
            nombre1 = input("Nombre del servidor A: ")
            nombre2 = input("Nombre del servidor B: ")

            if nombre1 not in servidores_red:
                servidores_red[nombre1] = ServidorCorreoAvanzado(nombre1)
            if nombre2 not in servidores_red:
                servidores_red[nombre2] = ServidorCorreoAvanzado(nombre2)

            servidores_red[nombre1].conectar_servidor(servidores_red[nombre2])
            print("Servidores conectados.")

        # 9. Mostrar red (todos los servidores conocidos)
        elif opcion == "9":
            print("Mostrando conexiones de todos los servidores:")
            if not servidores_red:
                print("(no hay servidores)")
            for s in servidores_red.values():
                s.mostrar_conexiones()

        # 10. Enviar mensaje por la red (BFS) desde el servidor origen REAL
        elif opcion == "10":
            origen = input("Servidor origen: ")
            destino = input("Servidor destino: ")

            if origen in servidores_red:
                servidores_red[origen].enviar_mensaje_red(origen, destino)
            else:
                print("El servidor origen no existe.")

        # salir
        elif opcion == "0":
            print("Saliendo del programa...")
            break

        else:
            print("Opcion invalida. Intente de nuevo.")

# Finalmente se puede ejecutar el programa con la terminal de python (con el boton run python file in dedicated terminal) que esta al lado de las opciones del boton de la flechita arriba a la derecha
# Aunque usted profe ya es un profesional y seguro lo sabe, lo digo por mis compañeros para que puedan abrir el archivo.

if __name__ == "__main__":
    iniciar_programa()
