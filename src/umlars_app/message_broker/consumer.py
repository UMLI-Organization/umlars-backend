from typing import Optional
import json

import pika

from umlars_app import settings
from umlars_app.exceptions import QueueUnavailableError, NotYetAvailableError, InputDataError
from umlars_app.utils.logging import get_new_sublogger
from umlars_app.rest.serializers import UmlFileTranslationStatusSerializer
from umlars_app.models import UmlFile, ProcessStatus
from umlars_app.utils.connections_utils import retry
from django.db import transaction


class RabbitMQConsumer:
    def __init__(self, queue_name: str, rabbitmq_host: str) -> None:
        self._logger = get_new_sublogger(self.__class__.__name__)
        self._queue_name = queue_name
        self._rabbitmq_host = rabbitmq_host
        self._connection = None
        self._channel = None
        self._queue = None

    @retry(exception_class_raised_when_all_attempts_failed=QueueUnavailableError)
    def connect_channel(self, rabbitmq_host: Optional[str] = None, queue_name: Optional[str] = None, is_queue_durable: bool = True) -> None:
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()

            rabbitmq_host = rabbitmq_host or self._rabbitmq_host
            queue_name = queue_name or self._queue_name

            self._logger.info(f"Connecting to RabbitMQ channel and queue: {rabbitmq_host}, {queue_name}...")
            credentials = pika.PlainCredentials(settings.MESSAGE_BROKER_USER, settings.MESSAGE_BROKER_PASSWORD)
            parameters = pika.ConnectionParameters(host=rabbitmq_host, port=settings.MESSAGE_BROKER_PORT, credentials=credentials)
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=queue_name, durable=is_queue_durable)

            self._logger.info("Connected to RabbitMQ channel and queue")
        except pika.exceptions.AMQPConnectionError as ex:
            error_message = f"Failed to connect to the channel: {ex}"
            self._logger.error(error_message)
            raise NotYetAvailableError(error_message) from ex
        except Exception as ex:
            self._logger.error(f"Unexpected error: {ex}")
            raise QueueUnavailableError("Unexpected error while connecting to the channel") from ex

    def _callback(self, ch, method, properties, body) -> None:
        self._logger.info(f"Callback execution started with body: {body}")

        try:
            serializer = self._deserialize_message(body)
            self._logger.info(f"Deserialized message: {serializer.validated_data}")
            self.process_message(serializer)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self._logger.info("Message acknowledged")
        except Exception as ex:
            self._logger.error(f"Failed to process message: {ex}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _deserialize_message(self, body: bytes) -> UmlFileTranslationStatusSerializer:
        serializer = UmlFileTranslationStatusSerializer(data=json.loads(body), partial=True)
        if not serializer.is_valid():
            error_message = f"Failed to deserialize message: {serializer.errors}"
            self._logger.error(error_message)
            raise InputDataError(error_message)
        return serializer

    def process_message(self, serializer: UmlFileTranslationStatusSerializer) -> None:
        if (message_from_translation_service := serializer.context.get('message')):
            self._logger.info(f"Message from translation service: {message_from_translation_service}")

        with transaction.atomic():
            try:
                uml_file = UmlFile.objects.get(id=serializer.validated_data['id'])
            except UmlFile.DoesNotExist as ex:
                error_message = f"Failed to get UmlFile: {ex}"
                self._logger.error(error_message)
                raise InputDataError(error_message) from ex
            
            self._logger.debug(f"Processing UmlFile: {uml_file}\n with status: {serializer.validated_data.get('state')} and current state: {uml_file.state}")
            self._logger.debug(f"Received process ID: {serializer.validated_data.get('last_process_id')} and current last process ID: {uml_file.last_process_id}")

            if serializer.validated_data.get('state') == ProcessStatus.RUNNING and uml_file.state != ProcessStatus.QUEUED:
                process_id = serializer.validated_data.get('last_process_id')
                last_process_id = uml_file.last_process_id
                if process_id is not None and last_process_id == process_id:
                    self._logger.info(f"Process ID {process_id} hase already been processed. Skipping...")
                    return

            serializer.instance = uml_file
            serializer.save()

    def start_consuming(self) -> None:
        try:
            self.connect_channel()

            self._channel.basic_consume(queue=self._queue_name, on_message_callback=self._callback, auto_ack=False)
            self._logger.info("Starting to consume messages")
            self._channel.start_consuming()
        except pika.exceptions.ConnectionClosed as ex:
            self._logger.error(f"Connection closed: {ex}")
            raise QueueUnavailableError("Connection closed by broker") from ex
        except QueueUnavailableError as ex:
            self._logger.error(f"Queue unavailable: {ex}")
            raise QueueUnavailableError("Queue unavailable") from ex
        except Exception as ex:
            self._logger.error(f"Unexpected error during messages consumption: {ex}")
            raise QueueUnavailableError("Unexpected error during messages consumption") from ex
