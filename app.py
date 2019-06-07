from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from utils import fetch_reply

app = Flask(__name__)

@app.route("/")
def hello():
    return "API Working"

@app.route("/sms", methods=['POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Fetch the message
    print(request.form)
    msg = request.form.get('Body')
    sender = request.form.get('From')

    # Create reply
    resp = MessagingResponse()

    result = fetch_reply(msg,sender)

    if type(result)==str:
        resp.message(result)

    else:
        resp.message('Here is your photo').media(result[0])
    
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)