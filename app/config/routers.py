from app.routers import user_router, reserva_router, perfil_router, payment_router

def include_routers(app):
    app.include_router(user_router.router)
    app.include_router(reserva_router.router) 
    app.include_router(perfil_router.router)
    app.include_router(payment_router.router)  # ← NUEVO ROUTER DE PAGOS