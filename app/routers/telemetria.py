from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from app.database import get_admin_client
from app.routers.viagens import get_usuario_logado
from app.services.gps_service import verificar_proximidade

router = APIRouter(prefix="/telemetria", tags=["Telemetria GPS"])


class CoordenadaInput(BaseModel):
    viagem_id: str
    latitude: float
    longitude: float


@router.post("/")
def receber_coordenada(
    dados: CoordenadaInput,
    authorization: str = Header(...)
):
    """
    Motorista ou script Python envia a posição atual do ônibus.
    O sistema grava no banco e verifica proximidade com as instituições.
    Se estiver a menos de 500m, dispara alerta via Realtime.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] not in ["admin", "fiscal", "motorista"]:
        raise HTTPException(
            status_code=403,
            detail="Sem permissão para enviar telemetria"
        )

    try:
        supabase = get_admin_client()

        # Grava a posição no banco
        supabase.table("telemetria").insert({
            "viagem_id": dados.viagem_id,
            "latitude": dados.latitude,
            "longitude": dados.longitude
        }).execute()

        # Verifica proximidade e dispara alertas se necessário
        alertas = verificar_proximidade(
            dados.viagem_id,
            dados.latitude,
            dados.longitude
        )

        resposta = {
            "mensagem": "Coordenada registrada",
            "latitude": dados.latitude,
            "longitude": dados.longitude
        }

        if alertas:
            resposta["alertas_disparados"] = alertas

        return resposta

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{viagem_id}/ultima-posicao")
def ultima_posicao(
    viagem_id: str,
    authorization: str = Header(...)
):
    """
    Retorna a última posição registrada do ônibus.
    Usado pelo Flutter para mostrar o ônibus no mapa.
    """
    get_usuario_logado(authorization)

    try:
        supabase = get_admin_client()

        posicao = supabase.table("telemetria") \
            .select("latitude, longitude, criado_em") \
            .eq("viagem_id", viagem_id) \
            .order("criado_em", desc=True) \
            .limit(1) \
            .execute()

        if not posicao.data:
            return {"mensagem": "Nenhuma posição registrada ainda"}

        return {"ultima_posicao": posicao.data[0]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))