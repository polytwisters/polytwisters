import json
from twilio.rest import Client


def main():
    with open("twilio_config.json") as file:
        config = json.load(file)
    account_sid = config["account_sid"]
    auth_token = config["auth_token"]
    from_number = config["from_number"]
    to_number = config["to_number"]
    body = """Render finished!"""
    client = Client(account_sid, auth_token)
    client.messages.create(from_=from_number, to=to_number, body=body)


if __name__ == "__main__":
    main()