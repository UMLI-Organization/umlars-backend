import json
from pika.channel import Channel



def create_message_data(**kwargs) -> dict:
    return kwargs


# TODO: get from env in DI and inject
def send_uploaded_file_message(channel: Channel, message_data: dict, queue_name: str= 'uploaded_files') -> None:
    try:
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(message_data))
    except Exception as ex:
        raise ValueError(f"Error while sending message: {ex}") from ex