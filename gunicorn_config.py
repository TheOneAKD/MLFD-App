import multiprocessing

def calculate_workers():
    return (multiprocessing.cpu_count() * 2) + 1

workers = calculate_workers()
worker_class = 'eventlet'
bind = '0.0.0.0:8000'
