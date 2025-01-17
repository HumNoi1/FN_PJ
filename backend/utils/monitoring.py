from functools import wraps
from prometheus_client import Counter, Histogram, start_http_server
import time
from typing import Optional
import logging
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ตั้งค่า logging
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUESTS = Counter(
    'milvus_requests_total',
    'Total number of requests by operation',
    ['operation']
)

LATENCY = Histogram(
    'milvus_operation_latency_seconds',
    'Time spent processing request',
    ['operation'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

ERROR_COUNT = Counter(
    'milvus_errors_total',
    'Total number of errors by operation',
    ['operation', 'error_type']
)

RESPONSE_TIME = Histogram(
    'api_response_time_seconds',
    'Time spent processing API requests',
    ['endpoint']
)

# ตั้งค่า OpenTelemetry tracing
def setup_tracing(service_name: str = "milvus-service"):
    """ตั้งค่า distributed tracing"""
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name
    }))
    
    processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

def track_operation(f):
    """
    Decorator สำหรับติดตามการทำงานของ operations
    - บันทึก metrics ด้วย Prometheus
    - สร้าง trace spans
    - บันทึก logs
    """
    @wraps(f)
    async def wrapped(*args, **kwargs):
        operation = f.__name__
        start_time = time.time()
        error: Optional[Exception] = None
        
        # สร้าง span สำหรับ operation นี้
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            operation,
            attributes={
                "args": str(args),
                "kwargs": str(kwargs)
            }
        ) as span:
            try:
                # เพิ่มจำนวน request
                REQUESTS.labels(operation=operation).inc()
                
                # เรียกฟังก์ชันจริง
                result = await f(*args, **kwargs)
                
                return result
                
            except Exception as e:
                error = e
                # บันทึก error metrics
                ERROR_COUNT.labels(
                    operation=operation,
                    error_type=type(e).__name__
                ).inc()
                
                # บันทึก error ใน span
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                
                raise
                
            finally:
                # บันทึกเวลาที่ใช้
                duration = time.time() - start_time
                LATENCY.labels(operation=operation).observe(duration)
                
                # บันทึก log
                log_data = {
                    "operation": operation,
                    "duration": duration,
                    "args": args,
                    "kwargs": kwargs
                }
                
                if error:
                    logger.error(
                        f"Operation {operation} failed",
                        extra=log_data,
                        exc_info=error
                    )
                else:
                    logger.info(
                        f"Operation {operation} completed",
                        extra=log_data
                    )
    
    return wrapped

# เริ่ม Prometheus HTTP server
def start_metrics_server(port: int = 8000):
    """เริ่ม server สำหรับ expose Prometheus metrics"""
    start_http_server(port)