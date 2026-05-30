from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY

# Cliente com service_role — usa no backend para operações administrativas
# (bypassa RLS, só usar no servidor, nunca expor pro Flutter)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Cliente com anon key — usa quando quiser respeitar o RLS
# (equivalente ao que o Flutter vai usar)
supabase_anon: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_admin_client() -> Client:
    return supabase_admin


def get_anon_client() -> Client:
    return supabase_anon