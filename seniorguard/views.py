import qrcode
import base64
from io import BytesIO
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db import connection
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from collections import defaultdict
from datetime import timedelta
from seniorguard.models import Device, Sensor, SensorType

# Create your views here.

def home(request):
    devices = Device.objects.all().order_by('-updated_at')
    connection.close()
    return render(request, "home.html", {"devices": devices})

@csrf_exempt
def dashboard(request, id):
    device = Device.objects.get(mac_address=id)
    # Busca todos os dados dos últimos 12h
    sensor_names = list(Sensor.objects.filter(device_id=id).order_by('sensor_type__order').values_list('sensor_type__name', flat=True).distinct())
    sensors_qs = Sensor.objects.filter(device=device).order_by('sensor_type__order', 'created_at')
    connection.close()
    sensor_history = {}
    latest_sensors = {}
    latest_time = None
    for name in sensor_names:
        grouped = defaultdict(list)
        # Filtra por tipo de sensor
        for s in sensors_qs.filter(sensor_type__name=name):
            # Agrupa por hora cheia
            bucket = s.created_at.replace(minute=0, second=0, microsecond=0)
            grouped[bucket].append(s.value)
            # Pega o último sensor para o "status atual"
            if name not in latest_sensors or s.created_at > latest_sensors[name].created_at:
                latest_sensors[name] = s
                if latest_time is None or s.created_at > latest_time:
                    latest_time = s.created_at
        # Calcula médias por hora e ordena pelo timestamp
        sensor_history[name] = [
            {
                "value": round(sum(values) / len(values), 1),  # média com 1 casa decimal
                "created_at": bucket.strftime('%Y-%m-%dT%H:00:00Z'),
            }
            for bucket, values in sorted(grouped.items())
        ]
    # Converte cada histórico para JSON para uso no template
    sensor_history_json = {k: json.dumps(v) for k, v in sensor_history.items()}
    # Considera atualizado se o dado mais recente for dos últimos 60 segundos
    updated_now = False
    if latest_time:
        updated_now = (timezone.now() - latest_time).total_seconds() < 60
    return render(request, "dashboard.html", {
        "device": device,
        "updated_now": updated_now,
        "sensors": latest_sensors.values(),
        "sensor_names": sensor_names,
        "sensor_history": sensor_history_json,
    })

@csrf_exempt
@database_sync_to_async
def update(request):
    """
    Recebe dados de sensores de um device.
    Cria o device se não existir.
    Atualiza os sensores e retorna seus intervalos válidos.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    mac_address = data.get('mac')
    if not mac_address:
        return JsonResponse({'error': 'MAC address não fornecido'}, status=400)

    # Cria ou atualiza o device
    device, _ = Device.objects.update_or_create(mac_address=mac_address)
    connection.close()
    updated_now = (timezone.now() - device.updated_at).total_seconds() < 60
    channel_layer = get_channel_layer() # notificar via websocket
    async_to_sync(channel_layer.group_send)(
        f"dashboard_{device.mac_address.replace(':','-')}",
        {
            "type": "device_update",
            "updated_now": updated_now,
            "updated_at": device.updated_at.isoformat()
        }
    )

    # Salva dados dos sensores (mantendo histórico de 12h)
    from datetime import timedelta
    if "sensors" in data:
        now = timezone.now()
        for sensor in data['sensors']:
            sensor_type_name = sensor.get('type')
            value = sensor.get('value')

            if not sensor_type_name or value is None:
                continue  # ignora entradas incompletas

            try:
                sensor_type = SensorType.objects.get(name=sensor_type_name)
                connection.close()
            except SensorType.DoesNotExist:
                continue  # ignora sensores não cadastrados

            # Remove dados mais antigos que 12h para este sensor/dispositivo
            Sensor.objects.filter(device=device,sensor_type=sensor_type,created_at__lt=now - timedelta(hours=12)).delete()
            connection.close()

            # Salva novo dado (não substitui)
            Sensor.objects.create(device=device,sensor_type=sensor_type,value=value,)
            connection.close()

            channel_layer = get_channel_layer() # notificar via websocket
            async_to_sync(channel_layer.group_send)(
                f"dashboard_{device.mac_address.replace(':','-')}",
                {
                    "type": "sensor_update",
                    "sensor_type": sensor_type.name,
                    "value": value,
                }
            )

    # Monta resposta com valores e intervalos válidos (apenas o dado mais recente de cada sensor)
    sensors = Sensor.objects.filter(device=device).order_by('sensor_type', '-created_at')
    connection.close()
    latest_sensors = {}
    for s in sensors:
        if s.sensor_type.name not in latest_sensors:
            latest_sensors[s.sensor_type.name] = s

    response_json = {}
    for name, s in latest_sensors.items():
        response_json[name] = s.value
        response_json[f"{name}_min"] = s.sensor_type.min_value
        response_json[f"{name}_max"] = s.sensor_type.max_value

    return JsonResponse(response_json)

@csrf_exempt
@require_POST
def edit_device_name(request, mac):
    """
    Atualiza o nome do dispositivo via AJAX.
    """
    try:
        device = Device.objects.get(mac_address=mac)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Dispositivo não encontrado'}, status=404)

    data = json.loads(request.body.decode('utf-8'))
    new_name = data.get('name', '').strip()

    if not new_name:
        return JsonResponse({'error': 'Nome inválido'}, status=400)

    device.name = new_name
    device.save(update_fields=['name', 'updated_at'])
    connection.close()
    return JsonResponse({'success': True, 'name': device.name})

# Retorna histórico de um sensor específico (AJAX)
@csrf_exempt
@require_GET
def sensor_history_api(request, mac, sensor_type):
    from datetime import timedelta
    from django.db.models.functions import TruncHour
    from django.db.models import Avg

    mac_colon = mac.replace('-', ':')
    try:
        device = Device.objects.get(mac_address=mac_colon)
        sensor_type_obj = SensorType.objects.get(name=sensor_type)
    except (Device.DoesNotExist, SensorType.DoesNotExist):
        return JsonResponse({'error': 'Dispositivo ou tipo de sensor não encontrado'}, status=404)

    # Consulta todos os dados do sensor e agrupa por hora
    sensors_qs = (
        Sensor.objects
        .filter(device=device, sensor_type=sensor_type_obj)
        .annotate(hour=TruncHour('created_at'))
        .values('hour')
        .annotate(avg_value=Avg('value'))
        .order_by('hour')
    )
    connection.close()

    history = [
        {'created_at': item['hour'].isoformat(), 'value': round(item['avg_value'], 2)}
        for item in sensors_qs
    ]
    return JsonResponse({'history': history})

# Deleta um dispositivo e seus sensores
@csrf_exempt
@require_POST
def delete_device(request, mac):    
    mac_colon = mac.replace('-', ':')
    try:
        device = Device.objects.get(mac_address=mac_colon)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Dispositivo não encontrado'}, status=404)

    # Deleta todos os sensores associados ao dispositivo
    Sensor.objects.filter(device=device).delete()
    # Deleta o dispositivo
    device.delete()
    connection.close()
    return JsonResponse({'success': True, 'message': 'Dispositivo e seus sensores foram deletados.'})

def device_qrcode(request, mac):
    device = get_object_or_404(Device, mac_address=mac)
    # URL do dashboard
    dashboard_url = request.build_absolute_uri(f"/dashboard/{device.mac_address}/")

    # Gera QRCode em memória
    qr = qrcode.make(dashboard_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return JsonResponse({"success": True, "qrcode": img_str})
