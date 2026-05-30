from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.cron_service import reativar_estudantes_suspensos

scheduler = BackgroundScheduler()

def iniciar_agendador():
    # Roda todo dia à meia-noite
    scheduler.add_job(
        reativar_estudantes_suspensos,
        CronTrigger(hour=0, minute=0),
        id="reativar_suspensos",
        replace_existing=True
    )
    scheduler.start()
    print("Agendador iniciado — reativação todo dia à meia-noite.")

def parar_agendador():
    scheduler.shutdown()