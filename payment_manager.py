

import json
import time
import stripe

from liqpay.liqpay3 import LiqPay
from utils_manager import UtilsManager


class PaymentManager:
    
    def commit_payment(self, request_dict):
        self.payment_request = PaymentRequest(request_dict)

        if self.payment_request.payment_service == "LiqPay":
            response = self.commit_liqpay_payment(self.payment_request)

            if response["result"] != "ok":
                return json.dumps({'result': response["result"], 'description': response["err_description"]}) 
            else:
                return json.dumps({'result': response["result"], 'description': "all good"}) 

        elif self.payment_request.payment_service == "Stripe":
            response = self.commit_stripe_payment(self.payment_request)

            if response['paid']:
                return json.dumps({'result': "ok", 'description': "all good"})
            else:
                return json.dumps({'result': "error", 'description': response["reason"]})

    def commit_liqpay_payment(self, payment_request):
        liqpay = LiqPay(payment_request.liqpay_public_key, payment_request.liqpay_private_key)

        response = liqpay.api("request", {
        "action"         : "subscribe",
        "version"        : "3",
        "amount"         : f"{payment_request.price_value}",
        "currency"       : f"{payment_request.currency}",
        "description"    : "{" + f"'user_id': '{payment_request.user_id}', 'plan_name': '{payment_request.plan_name}'" + "}",
        "card"           : f"{payment_request.card_number}",
        "card_exp_month" : f"{payment_request.month_expired}",
        "card_exp_year"  : f"{payment_request.year_expired}",
        "card_cvv"       : f"{payment_request.cvv}",
        "order_id"       : f"{payment_request.user_id}",
        "subscribe"             : "1",
        "subscribe_date_start"  : f"{payment_request.subscribe_date_start}",
        "subscribe_periodicity" : "month",
        })

        return response

    def commit_stripe_payment(self, payment_request):
        try:
            successful_states = ["incomplete", "trialing", "active"]
            stripe.api_key = payment_request.stripe_secret_key

            token_id = self.generate_card_token(
                payment_request.card_number,
                payment_request.month_expired,
                payment_request.year_expired,
                payment_request.cvv
            )

            product = stripe.Product.create(
                name = self.payment_request.plan_name
            )

            subsription_price = stripe.Price.create(
                unit_amount = int(payment_request.price_value * 100),
                currency = payment_request.currency,
                recurring = {"interval": "month"},
                product = product,
            )

            customer = stripe.Customer.create(
                description = f"StoryKids subscription with plan: {self.payment_request.plan_name}",
                id = payment_request.user_id,
                source = token_id,
            )

            result = stripe.Subscription.create(
            customer = customer,
            trial_period_days = 30,
            items = [
                    {"price": subsription_price.id},
                ],
            )

            result = {"paid": result.status in successful_states}
        except Exception as e:
            result = {"paid": False, "reason": str(e)}
        finally:
            return result

    def update_subscription(self, request_dict):
        if request_dict["paymentService"] == "LiqPay":
            return self.update_liqpay_subscription(request_dict)
        elif request_dict["paymentService"] == "Stripe":
            return self.update_stripe_subscription(request_dict)

    def update_liqpay_subscription(self, request_dict):
        self.payment_request = PaymentRequest(request_dict)
        liqpay = LiqPay(self.payment_request.liqpay_public_key, self.payment_request.liqpay_private_key)
        
        response = liqpay.api("request", {
        "action"         : "subscribe_update",
        "version"        : "3",
        "amount"         : f"{self.payment_request.price_value}",
        "currency"       : f"{self.payment_request.currency}",
        "description"    : "{" + f"'user_id': '{self.payment_request.user_id}', 'plan_name': '{self.payment_request.plan_name}', 'updated': 'true'" + "}",
        "card"           : f"{self.payment_request.card_number}",
        "card_exp_month" : f"{self.payment_request.month_expired}",
        "card_exp_year"  : f"{self.payment_request.year_expired}",
        "card_cvv"       : f"{self.payment_request.cvv}",
        "order_id"       : f"{self.payment_request.user_id}",
        })

        if (response['result'] == 'ok'):
            return json.dumps({'result': "ok", 'description': "all good"})
        else:
            return json.dumps({'result': "error", 'description': response["err_code"]})

    def update_stripe_subscription(self, request_dict):
        try:
            payment_request = PaymentRequest(request_dict)
            stripe.api_key = payment_request.stripe_secret_key

            token_id = self.generate_card_token(
                payment_request.card_number,
                payment_request.month_expired,
                payment_request.year_expired,
                payment_request.cvv
            )

            product = stripe.Product.create(
                name = payment_request.plan_name
            )

            subsription_price = stripe.Price.create(
                unit_amount = int(payment_request.price_value * 100),
                currency = payment_request.currency,
                recurring = {"interval": "month"},
                product = product,
            )

            stripe.Customer.modify(
                payment_request.user_id,
                source = token_id,
            )

            customer = stripe.Customer.retrieve(
                id = payment_request.user_id,
            )

            subscription_id = UtilsManager().subscription_to_id(request_dict)

            result = stripe.Subscription.modify(
                subscription_id,
                default_source = customer.default_source,
                items = [
                        {"price": subsription_price.id},
                    ],
            )

            result = json.dumps({'result': "ok", 'description': "all good"})
        except Exception as e:
            result = json.dumps({'result': "error", 'description': "No such subscription: unknown_id"})
        finally:
            return result

    def generate_card_token(self, cardnumber, expmonth, expyear, cvv):
        token = stripe.Token.create(
                card = {
                    "number": cardnumber,
                    "exp_month": int(expmonth),
                    "exp_year": int(expyear),
                    "cvc": cvv,
                })

        return token['id']

class PaymentRequest:
    def __init__(self, request_dict):
        self.time_stamp = time.time()
        self.cvv = request_dict["cvv"]
        self.user_id = request_dict["userId"]
        self.currency = request_dict["currency"]
        self.plan_name = request_dict["planName"]
        self.card_number = request_dict["cardNumber"]
        self.price_value = request_dict["priceValue"]
        self.year_expired = request_dict["yearExpired"]
        self.month_expired = request_dict["monthExpired"]
        self.payment_service = request_dict["paymentService"]
        self.stripe_secret_key = request_dict["stripeSecretKey"]
        self.liqpay_public_key = request_dict["liqpayPublicKey"]
        self.liqpay_private_key = request_dict["liqpayPrivateKey"]
        self.subscribe_date_start = request_dict["subscribeDateStart"]