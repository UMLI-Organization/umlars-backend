import logging
import concurrent.futures

from django.core.management.base import BaseCommand

from umlars_app.message_broker.consumer import RabbitMQConsumer
from umlars_app import settings


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Starts a multi-threaded consumer for RabbitMQ"

    def add_arguments(self, parser):
        parser.add_argument("numthreads", nargs="?", type=int, default=1, help="Number of threads to use for consuming messages")

    def handle(self, *args, **options):
        numthreads = options.get("numthreads", 1)
        self.stdout.write(f"Starting consumer with {numthreads} threads")
        logger.info("Starting consumer command called...")

        # Function to create and start a RabbitMQConsumer instance
        def consume():
            consumer = RabbitMQConsumer(queue_name=settings.MESSAGE_BROKER_QUEUE_TRANSLATED_MODELS_NAME, rabbitmq_host=settings.MESSAGE_BROKER_HOST)
            consumer.start_consuming()

        # Set up a multithreaded daemon to monitor the RabbitMQ queue
        with concurrent.futures.ThreadPoolExecutor(max_workers=numthreads) as executor:
            futures = [executor.submit(consume) for _ in range(numthreads)]
            try:
                for future in concurrent.futures.as_completed(futures):
                    future.result()  # This will wait for each consume function to finish
                logger.info("All threads completed")
            except Exception as e:
                logger.error("Error occurred: %s", e, exc_info=1)

        self.stdout.write(self.style.SUCCESS('Successfully started consumer daemon'))
