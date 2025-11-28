from fastapi import Request, Response
from prometheus_client import Counter, Histogram
import time

# Métricas HTTP básicas
HTTP_REQUESTS = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Excluir endpoints de métricas y health de las métricas
        if request.url.path in ['/metrics', '/health']:
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.time() - start_time
            
            # Registrar métricas
            HTTP_REQUESTS.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        
        return response