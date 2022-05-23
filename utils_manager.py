from liqpay.liqpay3 import LiqPay
from ast import literal_eval
import stripe

class UtilsManager:
    def json_to_dict(self, json_string):
        return literal_eval(json_string)

    def subscription_to_id(self, request_dict):
        try:
            stripe.api_key = request_dict["stripeSecretKey"]

            sub_list = stripe.Subscription.list(
                limit = 1,
                customer = request_dict['userId'],
            )

            return sub_list.data[0].id
        except:
            return "None"

    def check_if_user_exists(self, request_dict):
        liqpay_user_exists = self.check_if_user_exists_liqpay(request_dict)
        stripe_user_exists = self.check_if_user_exists_stripe(request_dict)


        if liqpay_user_exists["user_exists"] == "true":
            return f"{liqpay_user_exists}"
        else:
            return f"{stripe_user_exists}"

    def check_if_user_exists_liqpay(self, request_dict):
        result = dict()

        public_key = request_dict['liqpayPublicKey']
        private_key = request_dict['liqpayPrivateKey']

        liqpay = LiqPay(public_key, private_key)
        res = liqpay.api("request", {
        "action"        : "status",
        "version"       : "3",
        "order_id"      : request_dict['userId']
        })

        if res["status"] == "success" or res["status"] == "subscribed":
            result = UtilsManager().json_to_dict(res["description"])

            result["user_exists"] = "true"
            result["status"] = "success"
        elif res["status"] == "error" and res["err_code"] == "payment_not_found":
            result["user_exists"] = "false"
            result["status"] = "not_found"
        else:
            result["user_exists"] = "true"
            result["status"] = "not_paid"

        return result

    def check_if_user_exists_stripe(self, request_dict):
        stripe.api_key = request_dict["stripeSecretKey"]
        successful_states = ["incomplete", "trialing", "active"]
        
        try:
            sub_list = stripe.Subscription.list(
                limit = 1,
                customer = request_dict['userId'],
            )

            if sub_list.data[0].status in successful_states:
                return {"user_exists": "true", "status": "success"}
            else:
                return {"user_exists": "false", "status": "not_paid"}
        except:
            return {"user_exists": "false", "status": "not_found"}