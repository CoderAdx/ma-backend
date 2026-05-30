from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.database import get_admin_client

router = APIRouter(prefix="/viagens", tags=["Viagens"])


# --- Modelos ---

class CriarViagemInput(BaseModel):
    veiculo_id: str
    monitor_id: Optional[str] = None
    horario_limite_confirmacao: str  # formato "15:00"
    horario_partida_volta: Optional[str] = None  # formato "22:30"

class AdicionarParadaInput(BaseModel):
    viagem_id: str
    instituicao_id: str
    ordem: int

class ConfirmarPresencaInput(BaseModel):
    viagem_id: str
    estudante_id: str
    tipo: str  # 'ida', 'volta', 'ida_e_volta'


# --- Dependência: extrai e valida o token JWT ---
# O Flutter vai enviar o token no header assim:
# Authorization: Bearer eyJ...

def get_usuario_logado(authorization: str = Header(...)):
    """
    Extrai o usuário do token JWT enviado pelo Flutter.
    Retorna os dados do usuário ou lança 401 se inválido.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.replace("Bearer ", "")

    try:
        supabase = get_admin_client()
        resposta = supabase.auth.get_user(token)
        usuario_id = resposta.user.id

        usuario = supabase.table("usuarios") \
            .select("id, nome_completo, perfil, status") \
            .eq("id", usuario_id) \
            .single() \
            .execute()

        return usuario.data
    except Exception:
        raise HTTPException(status_code=401, detail="Token expirado ou inválido")


# --- Endpoints ---

@router.post("/")
def criar_viagem(
    dados: CriarViagemInput,
    authorization: str = Header(...)
):
    """
    Fiscal cria a viagem do dia.
    Só perfis 'fiscal' e 'admin' podem chamar esse endpoint.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] not in ["fiscal", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Apenas Fiscal ou Admin podem criar viagens"
        )

    if usuario["status"] == "suspenso":
        raise HTTPException(status_code=403, detail="Conta suspensa")

    try:
        supabase = get_admin_client()

        nova_viagem = supabase.table("viagens").insert({
            "veiculo_id": dados.veiculo_id,
            "fiscal_id": usuario["id"],
            "monitor_id": dados.monitor_id,
            "horario_limite_confirmacao": dados.horario_limite_confirmacao,
            "horario_partida_volta": dados.horario_partida_volta,
            "status": "aberta"
        }).execute()

        return {
            "mensagem": "Viagem criada com sucesso",
            "viagem": nova_viagem.data[0]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/paradas")
def adicionar_parada(
    dados: AdicionarParadaInput,
    authorization: str = Header(...)
):
    """
    Fiscal adiciona uma instituição como parada da viagem do dia.
    Pode chamar várias vezes para montar a rota completa.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] not in ["fiscal", "admin"]:
        raise HTTPException(status_code=403, detail="Apenas Fiscal ou Admin podem adicionar paradas")

    try:
        supabase = get_admin_client()

        parada = supabase.table("paradas_viagem").insert({
            "viagem_id": dados.viagem_id,
            "instituicao_id": dados.instituicao_id,
            "ordem": dados.ordem
        }).execute()

        return {
            "mensagem": "Parada adicionada",
            "parada": parada.data[0]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hoje")
def viagem_de_hoje(authorization: str = Header(...)):
    """
    Retorna a viagem do dia atual com veículo, paradas e contagem de confirmados.
    Todos os perfis podem consultar.
    """
    get_usuario_logado(authorization)

    try:
        supabase = get_admin_client()

        viagem = supabase.table("viagens") \
            .select("""
                id, status, data_viagem,
                horario_limite_confirmacao,
                horario_partida_volta,
                veiculos(placa, modelo, capacidade_assentos),
                paradas_viagem(ordem, instituicoes(nome, cidade))
            """) \
            .eq("data_viagem", "today") \
            .eq("status", "aberta") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not viagem.data:
            return {"mensagem": "Nenhuma viagem aberta para hoje"}

        return {"viagem": viagem.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirmar-presenca")
def confirmar_presenca(
    dados: ConfirmarPresencaInput,
    authorization: str = Header(...)
):
    """
    Estudante confirma presença na viagem.
    O trigger do banco já cuida da trava de lotação.
    Se o ônibus lotar, retorna erro LOTACAO_MAXIMA.
    """
    usuario = get_usuario_logado(authorization)

    try:
        supabase = get_admin_client()

        confirmacao = supabase.table("confirmacoes").insert({
            "viagem_id": dados.viagem_id,
            "estudante_id": dados.estudante_id,
            "tipo": dados.tipo,
            "status_embarque": "confirmado"
        }).execute()

        return {
            "mensagem": "Presença confirmada",
            "confirmacao": confirmacao.data[0]
        }
    except Exception as e:
        # O trigger lança LOTACAO_MAXIMA — capturamos e traduzimos
        if "LOTACAO_MAXIMA" in str(e):
            raise HTTPException(
                status_code=409,
                detail="Ônibus lotado. Você foi adicionado à lista de espera."
            )
        raise HTTPException(status_code=400, detail=str(e))