import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
CLIENTS_DIR = DATA_DIR / "clients"
INDEX_FILE = DATA_DIR / "index.json"
LOGS_DIR = BASE_DIR / "logs"
QUERIES_LOG = LOGS_DIR / "queries.log"

CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def normalize_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[áàä]", "a", name)
    name = re.sub(r"[éèë]", "e", name)
    name = re.sub(r"[íìï]", "i", name)
    name = re.sub(r"[óòö]", "o", name)
    name = re.sub(r"[úùü]", "u", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name

def slugify(name: str) -> str:
    return normalize_name(name).replace(" ", "-")

def load_index() -> dict:
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_index(index: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def require_non_empty(prompt: str) -> str:
    v = input(prompt).strip()
    if not v:
        print("No puede ir vacío.")
        return ""
    return v

def press_enter():
    input("Presiona ENTER para continuar...")

def list_clients(index: dict):
    if not index:
        print("No hay clientes registrados.")
        return
    print("LISTA DE CLIENTES")
    for k, filename in index.items():
        print(f"- {k} -> {filename}")

def create_client(index: dict):
    name = require_non_empty("Nombre del cliente: ")
    if not name:
        return

    key = normalize_name(name)
    if key in index:
        print("Ya existe ese cliente.")
        return

    tipo = input("Tipo (Persona/Negocio) [Persona]: ").strip() or "Persona"
    contacto = input("Contacto (tel/email opcional) [N/A]: ").strip() or "N/A"
    servicio = require_non_empty("Servicio (Telefonía/Internet/TV): ")
    if not servicio:
        return
    descripcion = require_non_empty("Descripción del servicio: ")
    if not descripcion:
        return

    customer_id = str(uuid.uuid4())
    filename = f"{customer_id}_{slugify(name)}.json"
    path = CLIENTS_DIR / filename

    cliente = {
        "customer_id": customer_id,
        "nombre": name,
        "tipo_cliente": tipo,
        "contacto": contacto,
        "fecha_alta": now_iso(),
        "solicitudes": [
            {
                "request_id": str(uuid.uuid4()),
                "servicio": servicio,
                "descripcion": descripcion,
                "fecha_solicitud": now_iso(),
                "canal": "call center"
            }
        ]
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cliente, f, ensure_ascii=False, indent=2)

    index[key] = filename
    save_index(index)

    print(f"Cliente creado: {name}")
    print(f"Archivo: {path}")

def find_client_file(index: dict, name: str):
    key = normalize_name(name)
    filename = index.get(key)
    if not filename:
        return None
    path = CLIENTS_DIR / filename
    if not path.exists():
        return None
    return path

def consult_client(index: dict):
    name = require_non_empty("Nombre del cliente: ")
    if not name:
        return

    path = find_client_file(index, name)
    if not path:
        print("Cliente no encontrado.")
        return

    with open(path, "r", encoding="utf-8") as f:
        cliente = json.load(f)

    print(json.dumps(cliente, ensure_ascii=False, indent=2))

    with open(QUERIES_LOG, "a", encoding="utf-8") as log:
        log.write(f"{now_iso()} | CONSULTA | {name}\n")

    print("Consulta registrada.")

def modify_client(index: dict):
    name = require_non_empty("Nombre del cliente: ")
    if not name:
        return

    path = find_client_file(index, name)
    if not path:
        print("Cliente no encontrado.")
        return

    with open(path, "r", encoding="utf-8") as f:
        cliente = json.load(f)

    print("1) Contacto")
    print("2) Agregar nueva solicitud de servicio")
    opt = input("Opción: ").strip()

    if opt == "1":
        nuevo = require_non_empty("Nuevo contacto: ")
        if not nuevo:
            return
        cliente["contacto"] = nuevo
        print("Contacto actualizado.")
    elif opt == "2":
        servicio = require_non_empty("Servicio (Telefonía/Internet/TV): ")
        if not servicio:
            return
        descripcion = require_non_empty("Descripción del servicio: ")
        if not descripcion:
            return
        cliente["solicitudes"].append({
            "request_id": str(uuid.uuid4()),
            "servicio": servicio,
            "descripcion": descripcion,
            "fecha_solicitud": now_iso(),
            "canal": "call center"
        })
        print("Solicitud agregada.")
    else:
        print("Opción inválida.")
        return

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cliente, f, ensure_ascii=False, indent=2)

    print("Cambios guardados.")

def delete_client(index: dict):
    name = require_non_empty("Nombre del cliente: ")
    if not name:
        return

    key = normalize_name(name)
    path = find_client_file(index, name)
    if not path:
        print("Cliente no encontrado.")
        return

    confirm = input(f"¿Borrar '{name}'? (si/no): ").strip().lower()
    if confirm != "si":
        print("Cancelado.")
        return

    os.remove(path)
    if key in index:
        del index[key]
        save_index(index)

    print("Cliente eliminado.")

def main():
    index = load_index()

    while True:
        print("AXANET/SKY - Gestor Clientes (Python)")
        print("1) Listar clientes")
        print("2) Consultar cliente")
        print("3) Crear cliente")
        print("4) Modificar cliente")
        print("5) Borrar cliente")
        print("0) Salir")

        opt = input("Elige opción: ").strip()

        if opt == "1":
            list_clients(index)
            press_enter()
        elif opt == "2":
            consult_client(index)
            press_enter()
        elif opt == "3":
            create_client(index)
            index = load_index()
            press_enter()
        elif opt == "4":
            modify_client(index)
            press_enter()
        elif opt == "5":
            delete_client(index)
            index = load_index()
            press_enter()
        elif opt == "0":
            print("Saliendo...")
            break
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()
Rename Code to app.py
