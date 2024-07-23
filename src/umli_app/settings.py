import os

BULK_UPLOAD_MODEL_DESCRIPTION = "Created from bulk load of files."
ADD_UML_MODELS_FORMSET_PREFIX = 'uml_models'
MESSAGE_BROKER_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
MESSAGE_BROKER_PORT = os.environ.get("RABBITMQ_NODE_PORT", 5672)
MESSAGE_BROKER_USER = os.environ.get("RABBITMQ_DEFAULT_USER", "admin")
MESSAGE_BROKER_PASSWORD = os.environ.get("RABBITMQ_DEFAULT_PASS", "admin")
MESSAGE_BROKER_QUEUE_NAME = os.environ.get("RABBITMQ_QUEUE_NAME", "uploaded_files")
