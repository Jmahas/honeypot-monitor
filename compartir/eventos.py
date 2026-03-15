import queue

# Permite pasar eventos del servidor a la GUI sin bloquear
event_queue = queue.Queue()