import logging
from flask import request
from time import time
from app import create_app, socketio

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create Flask logger
logger = logging.getLogger('flask.app')
logger.setLevel(logging.DEBUG)

app = create_app()

@app.before_request
def log_request_info():
    """Log HTTP request details."""
    logger.debug('Headers: %s', dict(request.headers))
    logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    if response.direct_passthrough:
        # For file downloads and streaming responses
        logger.debug('Response: [File or Stream Response]')
    else:
        # For regular responses
        try:
            logger.debug('Response: %s', response.get_data())
        except Exception as e:
            logger.debug('Response: [Could not log response data: %s]', str(e))
    return response

if __name__ == "__main__":
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=5001, 
        debug=True,
        log_output=True
    )