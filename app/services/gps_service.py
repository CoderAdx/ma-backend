import math
from datetime import datetime
from app.database import get_admin_client

# Raio médio da Terra em quilômetros
RAIO_TERRA_KM = 6371.0

# Distância em km para disparar o alerta de chegada (500 metros)
RAIO_ALERTA_KM = 0.5


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância em km entre dois pontos geográficos.
    Fórmula de Haversine — a mesma do documento de especificação.

    lat1, lon1 → posição atual do ônibus
    lat2, lon2 → posição da instituição de destino
    """
    # Converte graus para radianos
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Diferença entre as coordenadas
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    return RAIO_TERRA_KM * c


def verificar_proximidade(viagem_id: str, lat_onibus: float, lon_onibus: float):
    """
    Calcula a distância do ônibus até cada instituição da rota.
    Se estiver dentro de 500m, dispara alerta de chegada para
    os estudantes daquela instituição via Realtime.
    """
    supabase = get_admin_client()

    # Busca as paradas da viagem com coordenadas das instituições
    paradas = supabase.table("paradas_viagem") \
        .select("ordem, instituicoes(id, nome, latitude, longitude)") \
        .eq("viagem_id", viagem_id) \
        .execute()

    alertas_disparados = []

    for parada in paradas.data:
        inst = parada["instituicoes"]
        distancia = haversine(
            lat_onibus, lon_onibus,
            inst["latitude"], inst["longitude"]
        )

        if distancia <= RAIO_ALERTA_KM:
            # Verifica se já disparou alerta para essa instituição
            # nessa viagem (evita spam de notificações)
            alerta_existente = supabase.table("alertas_viagem") \
                .select("id") \
                .eq("viagem_id", viagem_id) \
                .eq("tipo", f"proximidade_{inst['id']}") \
                .execute()

            if not alerta_existente.data:
                # Dispara o alerta via Realtime
                supabase.table("alertas_viagem").insert({
                    "viagem_id": viagem_id,
                    "tipo": f"proximidade_{inst['id']}",
                    "payload": {
                        "instituicao": inst["nome"],
                        "distancia_km": round(distancia, 3),
                        "mensagem": f"O ônibus está se aproximando da {inst['nome']}. Prepare-se!"
                    }
                }).execute()

                alertas_disparados.append({
                    "instituicao": inst["nome"],
                    "distancia_km": round(distancia, 3)
                })

    return alertas_disparados