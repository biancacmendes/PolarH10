#!/usr/bin/env python3
"""
Varredura simples de dispositivos Bluetooth LE.
Lista todos os dispositivos encontrados e destaca os que parecem ser
sensores de frequência cardíaca (ex: Polar H10), mesmo quando o nome
não vem no pacote de advertising -- nesse caso, identifica pelo
serviço BLE padrão "Heart Rate" (UUID 0000180d-...).

Requisitos:
    pip install bleak

Uso:
    python3 scan_ble.py

IMPORTANTE: o Polar H10 só fica visível via Bluetooth enquanto está
ATIVO -- ou seja, com contato na pele (ou eletrodos bem umedecidos).
Parado e seco em cima da mesa, ele não anuncia nada.
"""

import asyncio
from bleak import BleakScanner

# UUID padrão do serviço BLE "Heart Rate" (usado por qualquer monitor
# cardíaco compatível com o padrão, incluindo o Polar H10)
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"


async def main():
    print("Procurando dispositivos Bluetooth LE (15 segundos)...\n")

    devices = await BleakScanner.discover(timeout=15, return_adv=True)

    if not devices:
        print("Nenhum dispositivo encontrado. Verifique se o Bluetooth "
              "está ligado no Mac.")
        return

    print(f"{len(devices)} dispositivo(s) encontrado(s):\n")
    print(f"{'Nome':25} {'Endereço':40} {'RSSI':>5}  Serviços")
    print("-" * 100)

    candidatos = []

    for address, (device, adv_data) in devices.items():
        name = device.name or "(sem nome)"
        rssi = adv_data.rssi if adv_data else "?"
        uuids = adv_data.service_uuids if adv_data else []
        uuids_str = ", ".join(uuids) if uuids else "-"
        print(f"{name:25} {address:40} {str(rssi):>5}  {uuids_str}")

        is_named_polar = "polar" in name.lower()
        has_hr_service = any(u.lower() == HEART_RATE_SERVICE_UUID for u in uuids)

        if is_named_polar or has_hr_service:
            candidatos.append((name, address, has_hr_service))

    if candidatos:
        print("\n>>> Possíveis sensores de frequência cardíaca encontrados:")
        for name, address, has_hr in candidatos:
            motivo = "nome contém 'Polar'" if "polar" in name.lower() else \
                     "anuncia serviço Heart Rate (mesmo sem nome)"
            print(f"    {name:25} -> {address}   ({motivo})")
        print("\nUse o endereço acima como DEVICE_ADDRESS no script de "
              "gravação de ECG.")
    else:
        print("\nNenhum candidato encontrado. Confirme que o H10 está "
              "com contato na pele/eletrodos umedecidos e tente de novo. "
              "Também vale rodar de novo, pois o advertising é "
              "intermitente e pode não ter sido capturado nesta janela.")


if __name__ == "__main__":
    asyncio.run(main())
