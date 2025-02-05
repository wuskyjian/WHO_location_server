import logging
from flask import request, g
from datetime import datetime
import json
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

# @app.before_request
# def log_request_info():
#     """Log HTTP request details."""
#     g.request_start_time = datetime.now()
    
#     logger.debug('\n' + '='*100)
#     logger.debug('【REQUEST START】 %s', datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
#     logger.debug('-'*100)
#     logger.debug('【PATH】 %s %s', request.method, request.full_path)
#     logger.debug('【HEADERS】\n%s', json.dumps(dict(request.headers), indent=2))
    
#     # Log request body if exists
#     if request.get_data():
#         try:
#             # Try to parse and format JSON body
#             body = request.get_json(silent=True)
#             if body:
#                 logger.debug('【BODY】\n%s', json.dumps(body, indent=2))
#             else:
#                 logger.debug('【BODY】\n%s', request.get_data())
#         except Exception:
#             logger.debug('【BODY】\n%s', request.get_data())
    
#     logger.debug('-'*100)

# @app.after_request
# def log_response_info(response):
#     """Log HTTP response details."""
#     duration = datetime.now() - g.request_start_time
    
#     logger.debug('【RESPONSE】 (%s ms)', int(duration.total_seconds() * 1000))
#     logger.debug('-'*100)
#     logger.debug('【STATUS】 %s', response.status)
#     logger.debug('【HEADERS】\n%s', json.dumps(dict(response.headers), indent=2))
    
#     if response.direct_passthrough:
#         logger.debug('【BODY】 [File or Stream Response]')
#     else:
#         try:
#             data = response.get_data()
#             if data:
#                 try:
#                     # Try to parse and format JSON response
#                     json_data = json.loads(data)
#                     logger.debug('【BODY】\n%s', json.dumps(json_data, indent=2))
#                 except json.JSONDecodeError:
#                     logger.debug('【BODY】\n%s', data)
#         except Exception as e:
#             logger.debug('【BODY】 [Could not log response data: %s]', str(e))
    
#     logger.debug('【REQUEST END】 %s', datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
#     logger.debug('='*100 + '\n')
    
#     return response

if __name__ == "__main__":
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=5001, 
        debug=True,
        log_output=True
    )