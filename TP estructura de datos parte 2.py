"""
Por el momento solo contiene:
- Clases: usuarios, mensajes, carpeta, servidor para correo
- Encapsulamiento con propiedades simples
- Interfaces para enviar, recibir y listar mensajes
- Manejo de carpetas y subcarpetas como árbol (recursivo)
- Movimiento de mensajes entre carpetas
"""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime
import itertools
import heapq
from collections import deque


_id_counter = itertools.count(1)

class Mensaje:
    """mensaje de correo simple"""
    def __init__(self, remitente: str, destinatario: str, asunto: str, cuerpo: str):
        self._id = next(_id_counter)
        self._remitente = remitente
        self._destinatario = destinatario
        self._asunto = asunto
        self._cuerpo = cuerpo
        self._timestamp = datetime.now()
        self._leido = False

    # Propiedades
    @property
    def id(self) -> int:
        return self._id

    @property
    def remitente(self) -> str:
        return self._remitente

    @property
    def destinatario(self) -> str:
        return self._destinatario

    @property
    def asunto(self) -> str:
        return self._asunto

    @property
    def cuerpo(self) -> str:
        return self._cuerpo

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def leido(self) -> bool: #Verdadero o falso 
        return self._leido

    def marcar_leido(self):
        self._leido = True

    def __repr__(self):
        return f"Mensaje(id={self._id}, from={self._remitente}, subj={self._asunto!r})"


class Carpeta:
    #Carpeta para contener mensajes y otras carpetas
 
    def __init__(self, nombre: str, padre: Optional[Carpeta] = None):
        self._nombre = nombre
        self._padre = padre
        self._subcarpetas: List[Carpeta] = []
        self._mensajes: List[Mensaje] = []

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def padre(self) -> Optional[Carpeta]:
        return self._padre

    @property
    def subcarpetas(self) -> List[Carpeta]:
        return list(self._subcarpetas)  # retorno copia para evitar modificacion directa

    @property
    def mensajes(self) -> List[Mensaje]:
        return list(self._mensajes)

    def crear_subcarpeta(self, nombre: str) -> Carpeta:
        carpeta = Carpeta(nombre, padre=self)
        self._subcarpetas.append(carpeta)
        return carpeta

    def agregar_mensaje(self, mensaje: Mensaje) -> None:
        self._mensajes.append(mensaje)

    def eliminar_mensaje_por_id(self, mensaje_id: int) -> Optional[Mensaje]:
        for i, m in enumerate(self._mensajes):
            if m.id == mensaje_id:
                return self._mensajes.pop(i)
        return None

    def buscar_mensajes_por_asunto(self, texto: str) -> List[Mensaje]:
        """Busqueda asunto."""
        texto_norm = texto.lower()
        resultados = [m for m in self._mensajes if texto_norm in m.asunto.lower()]
        for sub in self._subcarpetas:
            resultados.extend(sub.buscar_mensajes_por_asunto(texto))
        return resultados

    def buscar_mensajes_por_remitente(self, remitente: str) -> List[Mensaje]:
        remit_norm = remitente.lower()
        resultados = [m for m in self._mensajes if remit_norm == m.remitente.lower()]
        for sub in self._subcarpetas:
            resultados.extend(sub.buscar_mensajes_por_remitente(remitente))
        return resultados

    def ruta(self) -> str:
        partes = []
        actual = self
        while actual is not None:
            partes.append(actual.nombre)
            actual = actual.padre
        return "/".join(reversed(partes))

    def encontrar_subcarpeta_por_ruta(self, ruta_parcial: List[str]) -> Optional[Carpeta]:
        #Buscar subcarpeta  lista de nombres
    
        if not ruta_parcial:
            return self
        siguiente = ruta_parcial[0]
        for sub in self._subcarpetas:
            if sub.nombre == siguiente:
                return sub.encontrar_subcarpeta_por_ruta(ruta_parcial[1:])
        return None 

    def mover_mensaje_a(self, mensaje_id: int, destino: Carpeta) -> bool: 
        """Buscar y mover mensaje con id en este subarbol hacia la carpeta destino.
        Retorna True si se movio, False si no se encontro .
        """
        # primero intentar eliminar en este nodo
        mensaje = self.eliminar_mensaje_por_id(mensaje_id)
        if mensaje:
            destino.agregar_mensaje(mensaje)
            return True
        # si no esta aqui, recorrer subcarpetas
        for sub in self._subcarpetas:
            if sub.mover_mensaje_a(mensaje_id, destino):
                return True
        return False

    def listar_estructura(self, nivel: int = 0) -> None:
        print("  " * nivel + f"- {self.nombre} (mensajes: {len(self._mensajes)})")
        for m in self._mensajes:
            print("  " * (nivel + 1) + f"* {m}")
        for sub in self._subcarpetas:
            sub.listar_estructura(nivel + 1)

    def __repr__(self):
        return f"Carpeta({self._nombre})"


class Usuario:
    """Usuario simple con carpeta raiz (inbox) y operaciones para listar y mover mensajes."""
    def __init__(self, nombre: str, email: str):
        self._nombre = nombre
        self._email = email
        # carpeta raiz para este usuario
        self._root = Carpeta('root')
        # crear algunas carpetas por defecto
        self._inbox = self._root.crear_subcarpeta('inbox')
        self._sent = self._root.crear_subcarpeta('sent')
        self._trash = self._root.crear_subcarpeta('trash')

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def email(self) -> str:
        return self._email

    @property
    def root(self) -> Carpeta:
        return self._root

    @property
    def inbox(self) -> Carpeta:
        return self._inbox

    @property
    def sent(self) -> Carpeta:
        return self._sent

    @property
    def trash(self) -> Carpeta:
        return self._trash

    def listar_carpetas(self) -> None:
        print(f"Estructura de carpetas de {self.email}:")
        self._root.listar_estructura()

    def recibir_mensaje(self, mensaje: Mensaje, carpeta_destino: Optional[Carpeta] = None) -> None:
        if carpeta_destino is None:
            carpeta_destino = self._inbox
        carpeta_destino.agregar_mensaje(mensaje)

    def mover_mensaje(self, mensaje_id: int, ruta_destino: List[str]) -> bool:
        """Mover mensaje desde cualquier carpeta del arbol del usuario hacia la ruta_destino
        """
        destino = self._root.encontrar_subcarpeta_por_ruta(ruta_destino)
        if destino is None:
            return False
        return self._root.mover_mensaje_a(mensaje_id, destino)

    def buscar_por_asunto(self, texto: str) -> List[Mensaje]:
        return self._root.buscar_mensajes_por_asunto(texto)

    def buscar_por_remitente(self, remitente: str) -> List[Mensaje]:
        return self._root.buscar_mensajes_por_remitente(remitente)

    def __repr__(self):
        return f"Usuario({self._nombre}, {self._email})"


class ServidorCorreo:
    """Servidor de correo registra usuarios y entrega mensajes."""
    def __init__(self):
        self._usuarios: dict[str, Usuario] = {}

    def registrar_usuario(self, usuario: Usuario) -> None:
        self._usuarios[usuario.email] = usuario

    def enviar(self, remitente_email: str, destinatario_email: str, asunto: str, cuerpo: str) -> Optional[Mensaje]:
        """Crear el mensaje y entregarlo al destinatario Tambien guarda copia en 'sent'."""
        if remitente_email not in self._usuarios:
            print(f"Remitente {remitente_email} no registrado en el servidor.")
            return None
        if destinatario_email not in self._usuarios:
            print(f"Destinatario {destinatario_email} no registrado en el servidor. Entrega fallida.")
            return None
        mensaje = Mensaje(remitente_email, destinatario_email, asunto, cuerpo)
        destinatario = self._usuarios[destinatario_email]
        destinatario.recibir_mensaje(mensaje)
        # copia en sent del remitente
        remitente = self._usuarios[remitente_email]
        remitente.sent.agregar_mensaje(mensaje)
        return mensaje

    def listar_usuarios(self) -> None:
        print("Usuarios registrados:")
        for email, u in self._usuarios.items():
            print(f"- {u.nombre} <{email}>")

class ServidorCorreoAvanzado(ServidorCorreo):
    
    def __init__(self, nombre):
        super().__init__()
        self._nombre = nombre
        self._filtros: dict[str, str] = {}  # ejemplo: {"promo": "spam", "trabajo": "laboral"}
        self._cola_prioridad = []  # mensajes urgentes
        self._conexiones: dict[str, list[str]] = {}  # grafo de servidores

    def agregar_filtro(self, palabra_clave: str, carpeta_destino: str):
        """agrega un filtro automatico"""
        self._filtros[palabra_clave.lower()] = carpeta_destino.lower()

    def aplicar_filtros(self, usuario: Usuario, mensaje: Mensaje):
        """mueve automaticamente los mensajes segun filtros"""
        for palabra, carpeta in self._filtros.items():
            if palabra in mensaje.asunto.lower() or palabra in mensaje.cuerpo.lower():
                destino = usuario.root.encontrar_subcarpeta_por_ruta([carpeta])
                if destino:
                    usuario.mover_mensaje(mensaje.id, [carpeta])
                    print(f"Filtro aplicado: '{palabra}' movio mensaje a {carpeta}")
                    return
        print("No se aplico ningun filtro")

    def agregar_mensaje_urgente(self, mensaje: Mensaje, prioridad: int):
        """guarda mensajes urgentes en una cola"""
        heapq.heappush(self._cola_prioridad, (prioridad, mensaje))
        print(f"Mensaje urgente agregado con prioridad {prioridad}")

    def procesar_mensajes_urgentes(self):
        """procesa la cola de prioridad"""
        print("Procesando mensajes urgentes:")
        while self._cola_prioridad:
            prioridad, mensaje = heapq.heappop(self._cola_prioridad)
            print(f"Mensaje urgente (prioridad {prioridad}): {mensaje.asunto}")

    # Red de servidores

    def conectar_servidor(self, otro: ServidorCorreoAvanzado):
        """conecta este servidor con otro (grafo no dirigido)"""
        if self._nombre not in self._conexiones:
            self._conexiones[self._nombre] = []
        if otro._nombre not in self._conexiones:
            self._conexiones[otro._nombre] = []

        self._conexiones[self._nombre].append(otro._nombre)
        self._conexiones[otro._nombre].append(self._nombre)
        print(f"Servidores conectados: {self._nombre} <-> {otro._nombre}")

    def mostrar_conexiones(self):
        """muestra el grafo de servidores"""
        print("Red de servidores:")
        for serv, vecinos in self._conexiones.items():
            print(f"{serv}: {vecinos}")

    def enviar_mensaje_red(self, origen: str, destino: str):
        """simula envio de mensaje entre servidores usando BFS"""
        if origen not in self._conexiones or destino not in self._conexiones:
            print("Alguno de los servidores no existe en la red")
            return

        visitados = set()
        cola = deque([origen])
        print(f"Iniciando BFS desde {origen}")

        while cola:
            actual = cola.popleft()
            if actual == destino:
                print(f"Mensaje entregado correctamente de {origen} a {destino}")
                return
            visitados.add(actual)
            for vecino in self._conexiones.get(actual, []):
                if vecino not in visitados:
                    cola.append(vecino)
        print("No fue posible entregar el mensaje")