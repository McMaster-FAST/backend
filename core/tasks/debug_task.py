from celery import shared_task


# Debug Task for Celery Workers and RabbitMQk
@shared_task
def debug_task():
    print("Debug Task: Celery worker is running correctly.")
