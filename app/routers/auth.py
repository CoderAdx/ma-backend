from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from app.database import get_admin_client
from app.services.email_service import enviar_credenciais

router = APIRouter(prefix="/auth", tags=["Autenticação"])


# --- Modelos de entrada ---
# Pydantic valida os dados automaticamente antes de chegar na função.
# Se o Flutter mandar um JSON sem "email", o FastAPI já rejeita
# com erro 422 antes de você escrever qualquer if.

class LoginInput(BaseModel):
    email: EmailStr
    senha: str

class CriarUsuarioInput(BaseModel):
    email: EmailStr
    senha: str
    nome_completo: str
    perfil: str  # 'admin', 'fiscal', 'motorista', 'monitor', 'estudante'


# --- Endpoints ---

@router.post("/login")
def login(dados: LoginInput):
    """
    Autentica um usuário via Supabase Auth.
    Retorna o token JWT que o Flutter vai guardar e usar
    em todas as requisições seguintes.
    """
    try:
        supabase = get_admin_client()
        resposta = supabase.auth.sign_in_with_password({
            "email": dados.email,
            "password": dados.senha
        })

        usuario = supabase.table("usuarios") \
            .select("id, nome_completo, perfil, status") \
            .eq("id", resposta.user.id) \
            .single() \
            .execute()

        # Bloqueia login se estiver suspenso
        if usuario.data["status"] == "suspenso":
            raise HTTPException(
                status_code=403,
                detail="Conta suspensa. Aguarde o prazo de suspensão."
            )

        return {
            "access_token": resposta.session.access_token,
            "token_type": "bearer",
            "usuario": usuario.data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")


@router.post("/criar-usuario")
def criar_usuario(dados: CriarUsuarioInput):
    perfis_validos = ['admin', 'fiscal', 'motorista', 'monitor', 'estudante']
    if dados.perfil not in perfis_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Perfil inválido. Use um de: {perfis_validos}"
        )

    try:
        supabase = get_admin_client()
        resposta = supabase.auth.admin.create_user({
            "email": dados.email,
            "password": dados.senha,
            "user_metadata": {
                "nome_completo": dados.nome_completo,
                "perfil": dados.perfil
            },
            "email_confirm": True
        })

        # Envia email com as credenciais
        try:
            enviar_credenciais(
                email=dados.email,
                nome=dados.nome_completo,
                senha=dados.senha,
                perfil=dados.perfil
            )
        except Exception as email_error:
            # Email falhou mas usuário foi criado — não bloqueia
            print(f"Aviso: email não enviado — {email_error}")

        return {
            "mensagem": "Usuário criado com sucesso",
            "id": resposta.user.id,
            "email": resposta.user.email
        }


    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
def logout():
    """
    No Supabase o logout é feito no cliente (Flutter apaga o token).
    Esse endpoint existe por convenção REST.
    """
    return {"mensagem": "Logout realizado. Descarte o token no cliente."}

class ResetSenhaInput(BaseModel):
    email: EmailStr

@router.post("/reset-senha")
def reset_senha(dados: ResetSenhaInput):
    """
    Dispara o email de reset de senha via Supabase.
    O Supabase envia o link automaticamente.
    """
    try:
        supabase = get_admin_client()
        supabase.auth.reset_password_email(dados.email)
        return {"mensagem": "Email de redefinição enviado."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.delete("/deletar-usuario/{usuario_id}")
def deletar_usuario(usuario_id: str, authorization: str = Header(...)):
    """
    Remove o usuário do Supabase Auth.
    Só admin pode chamar.
    """
    usuario = get_usuario_logado(authorization)

    if usuario["perfil"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas Admin pode deletar usuários")

    try:
        supabase = get_admin_client()
        supabase.auth.admin.delete_user(usuario_id)
        return {"mensagem": "Usuário removido do Auth"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))