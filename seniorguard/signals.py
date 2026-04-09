from .models import SensorType

def create_sensor_type(sender, **kwargs):
    sensor_types = [
        {
            "name": "tmpA",
            "description": "Temperatura do ambiente de escritório (conforto térmico NR-17)",
            "unit": "°C",
            "min_value": 18,
            "max_value": 25,
            "order": 1
        },
        {
            "name": "umdA",
            "description": "Umidade relativa do ar em escritório (conforme ISO-9241)",
            "unit": "%",
            "min_value": 40,
            "max_value": 80,
            "order": 2
        },
        {
            "name": "rndA",
            "description": "Nível de ruído ambiente de escritório (conforto acústico NBR 10152)",
            "unit": "dB",
            "min_value": 0,
            "max_value": 65,
            "order": 3
        },
    ]

    for sensor in sensor_types:
        SensorType.objects.update_or_create(
            name=sensor["name"],
            defaults={
                "description": sensor["description"],
                "unit": sensor["unit"],
                "min_value": sensor["min_value"],
                "max_value": sensor["max_value"],
                "order": sensor["order"],
            },
        )
