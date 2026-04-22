import boto3
import socket
from botocore.exceptions import ClientError, NoCredentialsError

# ─────────────────────────────────────────
#  DATOS DEL ALUMNO
# ─────────────────────────────────────────
ALUMNO    = "Ariel Martínez"
MATRICULA = "Al3005455"
REGION    = "us-east-1"   # Cambia si tu ambiente usa otra región

# ─────────────────────────────────────────
#  DETECTAR AMBIENTE SEGÚN HOSTNAME
# ─────────────────────────────────────────
def detectar_ambiente() -> tuple[str, str]:
    """
    Lee el hostname de la máquina actual.
    Si contiene 'prod' → Producción / Production
    Cualquier otro caso → Desarrollo / Development
    Retorna (nombre_display, tag_value)
    """
    hostname = socket.gethostname().lower()
    if "prod" in hostname:
        return "Producción", "Production"
    return "Desarrollo", "Development"

AMBIENTE_DISPLAY, AMBIENTE_TAG = detectar_ambiente()

# ─────────────────────────────────────────
#  CLIENTE BOTO3
# ─────────────────────────────────────────
def get_client():
    """Crea y retorna un cliente EC2. Usa el rol IAM de la instancia automáticamente."""
    return boto3.client("ec2", region_name=REGION)

# ─────────────────────────────────────────
#  ENCABEZADO
# ─────────────────────────────────────────
def mostrar_encabezado():
    print("\n========================================")
    print(f"  Alumno:    {ALUMNO}")
    print(f"  Matrícula: {MATRICULA}")
    print(f"  Ambiente:  {AMBIENTE_DISPLAY}")
    print("========================================")

# ─────────────────────────────────────────
#  MENÚ
# ─────────────────────────────────────────
def mostrar_menu():
    mostrar_encabezado()
    print("  1. Listar instancias")
    print("  2. Iniciar instancia")
    print("  3. Detener instancia")
    print("  4. Reiniciar instancia")
    print("  5. Salir")
    print("========================================")

# ─────────────────────────────────────────
#  HELPER: OBTENER INSTANCIAS FILTRADAS
# ─────────────────────────────────────────
def obtener_instancias(ec2) -> list[dict]:
    """
    Retorna instancias filtradas por:
      - Environment = <AMBIENTE_TAG>
      - Owner       = <MATRICULA>
    """
    try:
        respuesta = ec2.describe_instances(
            Filters=[
                {"Name": "tag:Environment", "Values": [AMBIENTE_TAG]},
                {"Name": "tag:Owner",       "Values": [MATRICULA]},
            ]
        )
    except NoCredentialsError:
        print("\n[ERROR] No se encontraron credenciales de AWS.")
        print("        Verifica que la instancia tenga un rol IAM asignado.")
        return []
    except ClientError as e:
        print(f"\n[ERROR AWS] {e.response['Error']['Message']}")
        return []

    instancias = []
    for reserva in respuesta["Reservations"]:
        for inst in reserva["Instances"]:
            # Extraer el tag Name
            nombre = next(
                (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                "(sin nombre)"
            )
            instancias.append({
                "nombre":     nombre,
                "id":         inst["InstanceId"],
                "estado":     inst["State"]["Name"],
                "ip_privada": inst.get("PrivateIpAddress", "N/A"),
                "ip_publica": inst.get("PublicIpAddress",  "N/A"),
            })
    return instancias

# ─────────────────────────────────────────
#  HELPER: IMPRIMIR LISTA RESUMIDA (ID + Nombre)
# ─────────────────────────────────────────
def imprimir_lista_resumida(instancias: list[dict]):
    if not instancias:
        print("\n  No se encontraron instancias para este ambiente/matrícula.")
        return
    print()
    for i in instancias:
        print(f"  [{i['id']}]  {i['nombre']}  —  {i['estado']}")

# ─────────────────────────────────────────
#  OPCIÓN 1: LISTAR
# ─────────────────────────────────────────
def listar_instancias(ec2):
    instancias = obtener_instancias(ec2)
    if not instancias:
        return

    print(f"\n  Instancias en ambiente '{AMBIENTE_DISPLAY}':\n")
    for i in instancias:
        print(f"  Nombre:     {i['nombre']}")
        print(f"  ID:         {i['id']}")
        print(f"  Estado:     {i['estado']}")
        print(f"  IP Privada: {i['ip_privada']}")
        print(f"  IP Pública: {i['ip_publica']}")
        print("  ----------------------------")

# ─────────────────────────────────────────
#  OPCIÓN 2: INICIAR
# ─────────────────────────────────────────
def iniciar_instancia(ec2):
    instancias = obtener_instancias(ec2)
    imprimir_lista_resumida(instancias)
    if not instancias:
        return

    instance_id = input("\n  Ingresa el ID de la instancia a INICIAR: ").strip()
    if not instance_id:
        print("  [!] No ingresaste ningún ID.")
        return

    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"\n  ✅ Instancia {instance_id} enviada a iniciar.")
    except ClientError as e:
        print(f"\n  [ERROR] {e.response['Error']['Message']}")

# ─────────────────────────────────────────
#  OPCIÓN 3: DETENER
# ─────────────────────────────────────────
def detener_instancia(ec2):
    instancias = obtener_instancias(ec2)
    imprimir_lista_resumida(instancias)
    if not instancias:
        return

    instance_id = input("\n  Ingresa el ID de la instancia a DETENER: ").strip()
    if not instance_id:
        print("  [!] No ingresaste ningún ID.")
        return

    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"\n  ⛔ Instancia {instance_id} enviada a detener.")
    except ClientError as e:
        print(f"\n  [ERROR] {e.response['Error']['Message']}")

# ─────────────────────────────────────────
#  OPCIÓN 4: REINICIAR
# ─────────────────────────────────────────
def reiniciar_instancia(ec2):
    instancias = obtener_instancias(ec2)
    imprimir_lista_resumida(instancias)
    if not instancias:
        return

    instance_id = input("\n  Ingresa el ID de la instancia a REINICIAR: ").strip()
    if not instance_id:
        print("  [!] No ingresaste ningún ID.")
        return

    try:
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"\n  🔄 Instancia {instance_id} enviada a reiniciar.")
    except ClientError as e:
        print(f"\n  [ERROR] {e.response['Error']['Message']}")

# ─────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────
def main():
    ec2 = get_client()

    while True:
        mostrar_menu()
        opcion = input("  Seleccione una opción: ").strip()

        if opcion == "1":
            listar_instancias(ec2)
        elif opcion == "2":
            iniciar_instancia(ec2)
        elif opcion == "3":
            detener_instancia(ec2)
        elif opcion == "4":
            reiniciar_instancia(ec2)
        elif opcion == "5":
            mostrar_encabezado()
            print("  Hasta luego 👋")
            print("========================================\n")
            break
        else:
            print("\n  [!] Opción no válida. Intenta de nuevo.")

        input("\n  Presiona Enter para continuar...")

if __name__ == "__main__":
    main()