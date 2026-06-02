import resend
from app.config import RESEND_API_KEY

resend.api_key = RESEND_API_KEY


def enviar_credenciais(email: str, nome: str, senha: str, perfil: str):
    """
    Envia email com as credenciais de acesso ao novo usuário.
    Chamado sempre que o admin cria um usuário novo.
    """
    perfil_label = {
        'estudante': 'Estudante',
        'fiscal': 'Fiscal',
        'motorista': 'Motorista',
        'monitor': 'Monitor',
        'admin': 'Administrador',
    }.get(perfil, perfil)

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #1E6B3C; padding: 24px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">🎓 Maruim Acadêmico</h1>
            <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0 0;">
                Transporte Universitário Municipal
            </p>
        </div>

        <div style="background: #f9f9f9; padding: 32px; border-radius: 0 0 12px 12px;">
            <h2 style="color: #333;">Olá, {nome}!</h2>

            <p style="color: #555;">
                Sua conta no <strong>Maruim Acadêmico</strong> foi criada com sucesso.
                Abaixo estão suas credenciais de acesso:
            </p>

            <div style="background: white; border: 1px solid #e0e0e0; border-radius: 8px;
                        padding: 20px; margin: 24px 0;">
                <p style="margin: 0 0 8px 0; color: #888; font-size: 13px;">PERFIL</p>
                <p style="margin: 0 0 16px 0; font-weight: bold; color: #1E6B3C;">
                    {perfil_label}
                </p>

                <p style="margin: 0 0 8px 0; color: #888; font-size: 13px;">EMAIL</p>
                <p style="margin: 0 0 16px 0; font-weight: bold;">{email}</p>

                <p style="margin: 0 0 8px 0; color: #888; font-size: 13px;">
                    SENHA TEMPORÁRIA
                </p>
                <p style="margin: 0; font-size: 24px; font-weight: bold;
                           letter-spacing: 4px; color: #333;">{senha}</p>
            </div>

            <div style="background: #fff3cd; border: 1px solid #ffc107;
                        border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                <p style="margin: 0; color: #856404; font-size: 13px;">
                    ⚠️ <strong>Importante:</strong> Esta é uma senha temporária.
                    Após o primeiro acesso, altere sua senha nas configurações do app.
                </p>
            </div>

            <p style="color: #555;">
                Baixe o aplicativo <strong>Maruim Acadêmico</strong> e faça login
                com as credenciais acima.
            </p>

            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 24px 0;">

            <p style="color: #888; font-size: 12px; margin: 0;">
                Prefeitura Municipal de Maruim/SE —
                Secretaria de Transporte e Educação
            </p>
        </div>
    </div>
    """

    resend.Emails.send({
        "from": "Maruim Acadêmico <noreply@adxdev.com.br>",
        "to": [email],
        "subject": "Suas credenciais de acesso — Maruim Acadêmico",
        "html": html,
    })


def enviar_reset_senha(email: str, nome: str, link: str):
    """
    Envia email com link para redefinir senha.
    """
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #1E6B3C; padding: 24px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">🎓 Maruim Acadêmico</h1>
        </div>

        <div style="background: #f9f9f9; padding: 32px; border-radius: 0 0 12px 12px;">
            <h2 style="color: #333;">Olá, {nome}!</h2>

            <p style="color: #555;">
                Recebemos uma solicitação para redefinir a senha da sua conta.
            </p>

            <div style="text-align: center; margin: 32px 0;">
                <a href="{link}"
                   style="background-color: #1E6B3C; color: white; padding: 16px 32px;
                          border-radius: 8px; text-decoration: none; font-weight: bold;
                          font-size: 16px;">
                    Redefinir Senha
                </a>
            </div>

            <p style="color: #888; font-size: 13px;">
                Se você não solicitou a redefinição de senha, ignore este email.
                O link expira em 1 hora.
            </p>

            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 24px 0;">

            <p style="color: #888; font-size: 12px; margin: 0;">
                Prefeitura Municipal de Maruim/SE —
                Secretaria de Transporte e Educação
            </p>
        </div>
    </div>
    """

    resend.Emails.send({
        "from": "Maruim Acadêmico <noreply@adxdev.com.br>",
        "to": [email],
        "subject": "Redefinição de senha — Maruim Acadêmico",
        "html": html,
    })