import multiprocessing

# Determine the number of CPU cores
workers = multiprocessing.cpu_count() * 2 + 1

# Use eventlet worker class
worker_class = 'eventlet'

# Specify the host and port
bind = '0.0.0.0:8000'

# Number of worker threads
threads = 4

# Set maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Logging configuration
loglevel = 'info'
accesslog = '-'
errorlog = '-'
