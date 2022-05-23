import flask
from flask import jsonify
from flask import request
from ast import literal_eval

from utils_manager import UtilsManager
from payment_manager import PaymentManager

server_app = flask.Flask(__name__)


@server_app.route('/', methods=['GET'])
def home():
    return "<p>Server to provide payment functionality to an unnamed service</p>"

@server_app.route('/payment', methods=['POST', 'GET'])
def payment():
    response = ""
    request_dict = request_to_dict(request)

    if request_dict['type'] == 'payment':
        response = PaymentManager().commit_payment(request_dict)
    elif request_dict['type'] == 'check':
        response = UtilsManager().check_if_user_exists(request_dict)
    elif request_dict['type'] == 'update':
        response = PaymentManager().update_subscription(request_dict)
    else:
        response = f"Unsupported action: {request_dict['type']}"

    response = jsonify(response)
    add_headers(response)
    return response

def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')

def request_to_dict(request):
    request_bytes = request.data.decode('utf-8')
    return literal_eval(request_bytes) 


if (__name__ == "__main__"):
    server_app.run()
