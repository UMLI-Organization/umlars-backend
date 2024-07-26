import json
from typing import Optional

import pika
from contextlib import contextmanager

from umlars_app import settings
from umlars_app.exceptions import QueueUnavailableError
from umlars_app.utils.logging import get_new_sublogger
from umlars_app.rest.serializers import UmlModelTranslationQueueMessageSerializer
from umlars_app.models import UmlModel


class MessageBrokerProducer:
    def __init__(self, queue_name: str, rabbitmq_host: str) -> None:
        self._logger = get_new_sublogger(self.__class__.__name__)
        self._queue_name = queue_name
        self._rabbitmq_host = rabbitmq_host
        self._connection = None
        self._channel = None
        self._queue = None

    @contextmanager
    def connect_channel(self, rabbitmq_host: Optional[str] = None, queue_name: Optional[str] = None, is_queue_durable: bool = True, reset_connection: bool = False, close_connection: bool = False) -> None:
        try:
            if not self._connection or reset_connection or self._connection.is_closed:
                rabbitmq_host = rabbitmq_host or self._rabbitmq_host
                queue_name = queue_name or self._queue_name

                self._connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=rabbitmq_host,
                    port=settings.MESSAGE_BROKER_PORT,
                    credentials=pika.PlainCredentials(
                        username=settings.MESSAGE_BROKER_USER,
                        password=settings.MESSAGE_BROKER_PASSWORD
                    )
                ))
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=queue_name, durable=is_queue_durable)
            self._logger.info("Connected to RabbitMQ channel and queue")
            yield self._channel
        except pika.exceptions.AMQPConnectionError as ex:
            self._logger.error(f"Failed to connect to the channel: {ex}")
            raise QueueUnavailableError("Failed to connect to the channel") from ex
        except Exception as ex:
            self._logger.error(f"Unexpected error: {ex}")
            raise QueueUnavailableError("Unexpected error while connecting to the channel") from ex

        finally:
            if close_connection:
                self._connection.close()


    def send_message(self, message_data: dict) -> None:
        with self.connect_channel(close_connection=True):
            try:

                self._channel.basic_publish(
                    exchange='',
                    routing_key=self._queue_name,
                    body=json.dumps(message_data),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # make message persistent
                    )
                )
                self._logger.info("Message sent")
            except Exception as ex:
                self._logger.error(f"Error while sending message: {ex}")
                raise ValueError(f"Error while sending message: {ex}") from ex


def create_message_data(model: UmlModel) -> dict:
    return UmlModelTranslationQueueMessageSerializer(model).data


def send_uploaded_model_message(message_data: dict, producer: Optional[MessageBrokerProducer] = None, queue_name: str = settings.MESSAGE_BROKER_QUEUE_NAME) -> None:
    try:
        if producer is None:
            producer = MessageBrokerProducer(queue_name=queue_name, rabbitmq_host=settings.MESSAGE_BROKER_HOST)

        producer.send_message(message_data)
    except Exception as ex:
        raise ValueError(f"Error while sending message: {ex}") from ex