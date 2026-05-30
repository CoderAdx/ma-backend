from datetime import datetime, timedelta
from app.database import get_admin_client

def reativar_estudantes_suspensos():
    """
    Verifica estudantes suspensos há mais de 3 dias e reativa.
    Chamado pelo agendador todo dia à meia-noite.
    """
    supabase = get_admin_client()

    # Busca todas as penalidades aprovadas de estudantes suspensos
    # A lógica: se a penalidade mais recente tem mais de 3 dias,
    # o prazo de suspensão foi cumprido
    tres_dias_atras = (datetime.utcnow() - timedelta(days=3)).isoformat()

    # Busca usuários suspensos
    suspensos = supabase.table("usuarios") \
        .select("id") \
        .eq("status", "suspenso") \
        .execute()

    if not suspensos.data:
        print(f"[{datetime.now()}] Nenhum estudante suspenso.")
        return

    reativados = 0

    for usuario in suspensos.data:
        # Verifica a penalidade mais recente desse usuário
        estudante = supabase.table("estudantes") \
            .select("id") \
            .eq("usuario_id", usuario["id"]) \
            .single() \
            .execute()

        if not estudante.data:
            continue

        ultima_penalidade = supabase.table("penalidades") \
            .select("criado_em") \
            .eq("estudante_id", estudante.data["id"]) \
            .eq("status", "aprovada") \
            .order("criado_em", desc=True) \
            .limit(1) \
            .execute()

        if not ultima_penalidade.data:
            continue

        data_ultima = ultima_penalidade.data[0]["criado_em"]

        # Se a última penalidade foi há mais de 3 dias, reativa
        if data_ultima <= tres_dias_atras:
            supabase.table("usuarios") \
                .update({"status": "ativo"}) \
                .eq("id", usuario["id"]) \
                .execute()

            # Zera os pontos para começar do zero após suspensão
            supabase.table("estudantes") \
                .update({"pontos_penalidade": 0}) \
                .eq("id", estudante.data["id"]) \
                .execute()

            reativados += 1
            print(f"[{datetime.now()}] Usuário {usuario['id']} reativado.")

    print(f"[{datetime.now()}] Reativação concluída. {reativados} estudante(s) reativado(s).")