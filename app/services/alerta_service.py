from datetime import datetime
from app.database import get_admin_client

def verificar_faltantes(viagem_id: str) -> list:
    """
    Cruza confirmados para volta vs embarcados.
    Retorna lista de estudantes que confirmaram mas não embarcaram.
    """
    supabase = get_admin_client()

    # Busca confirmados para volta que ainda não embarcaram
    faltantes = supabase.table("confirmacoes") \
        .select("""
            estudantes(
                usuarios(nome_completo)
            )
        """) \
        .eq("viagem_id", viagem_id) \
        .in_("tipo", ["volta", "ida_e_volta"]) \
        .eq("status_embarque", "confirmado") \
        .execute()

    if not faltantes.data:
        return []

    nomes = [
        f["estudantes"]["usuarios"]["nome_completo"]
        for f in faltantes.data
    ]

    return nomes


def disparar_alerta_faltantes(viagem_id: str) -> dict:
    """
    Verifica faltantes e grava o alerta na tabela de alertas.
    O Supabase Realtime detecta o INSERT e notifica todos os
    clientes Flutter inscritos naquela viagem automaticamente.
    """
    supabase = get_admin_client()
    faltantes = verificar_faltantes(viagem_id)

    if not faltantes:
        return {"alerta": False, "mensagem": "Todos embarcaram!"}

    # Grava o alerta — o Realtime do Supabase dispara para o Flutter
    supabase.table("alertas_viagem").insert({
        "viagem_id": viagem_id,
        "tipo": "faltantes",
        "payload": {"nomes": faltantes, "total": len(faltantes)},
        "criado_em": datetime.utcnow().isoformat()
    }).execute()

    return {
        "alerta": True,
        "total_faltantes": len(faltantes),
        "nomes": faltantes
    }