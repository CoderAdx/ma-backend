from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.database import get_admin_client
from app.routers.viagens import get_usuario_logado
from app.services.cron_service import reativar_estudantes_suspensos






router = APIRouter(prefix="/penalidades", tags=["Penalidades"])


@router.post("/admin/rodar-reativacao")
def rodar_reativacao_manual(authorization: str = Header(...)):
    """
    Endpoint temporário para testar o cron job manualmente.
    Remover antes de ir para produção.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas Admin")

    reativar_estudantes_suspensos()
    return {"mensagem": "Reativação executada manualmente"}

# --- Modelos ---

class AplicarPenalidadeInput(BaseModel):
    estudante_id: str
    descricao: str
    pontos: int

class AtualizarStatusInput(BaseModel):
    status: str  # 'aprovada' ou 'cancelada'


# --- Endpoints ---

@router.post("/")
def aplicar_penalidade(
    dados: AplicarPenalidadeInput,
    authorization: str = Header(...)
):
    """
    Fiscal/Admin aplicam penalidade direto (status: aprovada).
    Monitor sugere penalidade (status: pendente).
    O trigger do banco cuida de somar os pontos automaticamente.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] not in ["admin", "fiscal", "monitor"]:
        raise HTTPException(
            status_code=403,
            detail="Sem permissão para aplicar penalidades"
        )

    if dados.pontos <= 0:
        raise HTTPException(
            status_code=400,
            detail="Pontos devem ser maiores que zero"
        )

    # Monitor sugere — fica pendente até fiscal aprovar
    # Fiscal e Admin aplicam direto — já entra aprovada
    status_inicial = "pendente" if usuario["perfil"] == "monitor" else "aprovada"

    try:
        supabase = get_admin_client()

        penalidade = supabase.table("penalidades").insert({
            "estudante_id": dados.estudante_id,
            "aplicado_por": usuario["id"],
            "descricao": dados.descricao,
            "pontos": dados.pontos,
            "status": status_inicial
        }).execute()

        # Busca os pontos atuais do estudante para retornar no response
        estudante = supabase.table("estudantes") \
            .select("pontos_penalidade") \
            .eq("id", dados.estudante_id) \
            .single() \
            .execute()

        return {
            "mensagem": f"Penalidade {'sugerida' if status_inicial == 'pendente' else 'aplicada'} com sucesso",
            "penalidade": penalidade.data[0],
            "pontos_atuais": estudante.data["pontos_penalidade"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{penalidade_id}")
def atualizar_status_penalidade(
    penalidade_id: str,
    dados: AtualizarStatusInput,
    authorization: str = Header(...)
):
    """
    Fiscal ou Admin aprovam ou cancelam uma penalidade pendente.
    Ao aprovar, o trigger soma os pontos automaticamente.
    Ao cancelar uma aprovada, o trigger remove os pontos.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] not in ["admin", "fiscal"]:
        raise HTTPException(
            status_code=403,
            detail="Apenas Fiscal ou Admin podem aprovar/cancelar penalidades"
        )

    if dados.status not in ["aprovada", "cancelada"]:
        raise HTTPException(
            status_code=400,
            detail="Status inválido. Use 'aprovada' ou 'cancelada'"
        )

    try:
        supabase = get_admin_client()

        penalidade = supabase.table("penalidades") \
            .update({"status": dados.status}) \
            .eq("id", penalidade_id) \
            .execute()

        if not penalidade.data:
            raise HTTPException(status_code=404, detail="Penalidade não encontrada")

        return {
            "mensagem": f"Penalidade {dados.status} com sucesso",
            "penalidade": penalidade.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pendentes")
def listar_pendentes(authorization: str = Header(...)):
    """
    Lista todas as penalidades pendentes de aprovação.
    Só Fiscal e Admin visualizam.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] not in ["admin", "fiscal"]:
        raise HTTPException(
            status_code=403,
            detail="Apenas Fiscal ou Admin visualizam pendentes"
        )

    try:
        supabase = get_admin_client()

        pendentes = supabase.table("penalidades") \
            .select("""
                id, descricao, pontos, criado_em,
                estudantes(
                    usuarios(nome_completo)
                ),
                aplicado_por_usuario:usuarios!penalidades_aplicado_por_fkey(
                    nome_completo, perfil
                )
            """) \
            .eq("status", "pendente") \
            .order("criado_em", desc=False) \
            .execute()

        return {
            "total": len(pendentes.data),
            "pendentes": pendentes.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/estudante/{estudante_id}")
def historico_estudante(
    estudante_id: str,
    authorization: str = Header(...)
):
    """
    Histórico completo de penalidades de um estudante.
    Estudante vê só o próprio. Operadores veem qualquer um.
    """
    usuario = get_usuario_logado(authorization)

    # Estudante só pode ver o próprio histórico
    if usuario["perfil"] == "estudante":
        supabase = get_admin_client()
        estudante = supabase.table("estudantes") \
            .select("id") \
            .eq("usuario_id", usuario["id"]) \
            .single() \
            .execute()

        if estudante.data["id"] != estudante_id:
            raise HTTPException(
                status_code=403,
                detail="Você só pode ver o próprio histórico"
            )

    try:
        supabase = get_admin_client()

        historico = supabase.table("penalidades") \
            .select("id, descricao, pontos, status, criado_em") \
            .eq("estudante_id", estudante_id) \
            .order("criado_em", desc=True) \
            .execute()

        estudante = supabase.table("estudantes") \
            .select("pontos_penalidade, usuarios(nome_completo, status)") \
            .eq("id", estudante_id) \
            .single() \
            .execute()

        return {
            "estudante": estudante.data["usuarios"]["nome_completo"],
            "status_conta": estudante.data["usuarios"]["status"],
            "pontos_acumulados": estudante.data["pontos_penalidade"],
            "pontos_para_suspensao": max(0, 100 - estudante.data["pontos_penalidade"]),
            "historico": historico.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))