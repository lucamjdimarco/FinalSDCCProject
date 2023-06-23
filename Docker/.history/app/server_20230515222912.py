from flask import Flask, request, render_template, send_file, redirect, jsonify, url_for
import os
import pika
import json
from markupsafe import escape
import base64
import boto3
import urllib
import uuid

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['EDITED_FOLDER'] = 'static/edited'

# Definisci le credenziali per l'accesso ad S3
ACCESS_KEY_ID = 'ASIAQEZ3HMBUN3EL5LV6'
ACCESS_KEY = 'ZnLsayaP4u+9r8okmga8MqTAMyNmNeOSgw6978k8'
SESSION_TOKEN = 'FwoGZXIvYXdzEAYaDBUs7QhKJWtpMfRlQyK+AYDgfYQNdrifmUVOzQgQfM9a76mwviHPTxgEo8UmjvlBcRfOvokExslMpXlt4BSb2X1tYgkyXAUcYAXabIjpu7hNbgMwsRUZu2ljhWLMY6iJ5h5KbBZ4vL9eKxrNtZ4h9qT7sds767J1BX+flmeWxnowp4KWuSU12tGXf0OKk2rqdB3HiXJDNEbtNRBMuHobNMqjUyiomeabhAAj5pPkNE9RvfCl3QTlH+WfCOOTsHgjN+AMA4Z+JbfzkYYDm8QooKeKowYyLRgntnz1rqqHDLzGji/FE8XecNVn5B3YoKMWtdCo+lQDo3YyKHR6ys4ZctJaKg=='
bucket_name = 'photosdcc'
folder_name = 'photos/'
s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_KEY,
    aws_session_token=SESSION_TOKEN
)

# VARIABILE AMBIENTE PER I NOMI
app.config['NOMI'] = []

# ------------------CLASS----------------------------
class ServerRPCClass(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        
        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if  self.corr_id == props.correlation_id:
            self.response = body
            s3.download_file(bucket_name, folder_name + body, os.path.join(app.config['EDITED_FOLDER'],'test.jpg'))

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n))
        self.connection.process_data_events(time_limit=None)
        return int(self.response)
    

# ------------------END CLASS------------------------

server_rpc = ServerRPCClass()

# ----------------------------------------------
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
#channel = connection.channel()
#result = channel.queue_declare(queue='', exclusive=True)
#callback_queue = result.method.queue
#----------------------------------------------
# def on_response(ch, method, props, body):
#         global corr_id
#         global response
#         if  corr_id == props.correlation_id:
#             response = body
#             s3.download_file(bucket_name, folder_name + body, os.path.join(app.config['EDITED_FOLDER'],'test.jpg'))

# def call(filename):
#         global corr_id
#         global response
#         response = None
#         corr_id = str(uuid.uuid4())
#         channel.basic_publish(
#             exchange='',
#             routing_key='rpc_queue',
#             properties=pika.BasicProperties(
#                 reply_to=callback_queue,
#                 correlation_id=corr_id,
#             ),
#             body=str(filename))
#         connection.process_data_events(time_limit=None)
#         return response

#----------------------------------------------

#CALLBACK DI CONSUMER
# def callback(ch, method, properties, body):
#     filename=body.decode('utf-8')
#     s3.download_file(bucket_name, folder_name + filename, os.path.join(app.config['EDITED_FOLDER'],'test.jpg'))
#     channel.basic_ack(delivery_tag=method.delivery_tag)
    
    #channel.queue_purge('coda_elaborati')
    # confronta il delivery tag del messaggio corrente con quello dell'ultimo messaggio processato
    # if method.delivery_tag != last_delivery_tag_processed + 1:
    #     ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    # else:
    #     print("Messaggio corretto!")
    #     ch.basic_ack(delivery_tag=method.delivery_tag)
    #     last_delivery_tag_processed = method.delivery_tag
    
    #return render_template('index.html')

#def start_consuming(): 

    
    #channel.start_consuming()

#PRODUCER
def sendPhoto_to_rabbitmq(filename):
    response = server_rpc.call(filename)
    #channel.basic_consume(queue=callback_queue, on_message_callback=on_response, auto_ack=True)
    #channel.basic_publish(exchange='', routing_key='coda_foto', body=filename)

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    
    nomi = []
    if request.method == 'POST':
        #ciclo per eliminare tutto ciò che è contenuto nella cartella UPLOAD
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))       

        #ciclo per eliminare tutto ciò che è contenuto nella cartella EDITED
        for filename in os.listdir(app.config['EDITED_FOLDER']):
            file_path = os.path.join(app.config['EDITED_FOLDER'], filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        file = request.files['file']
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        #upload su S3
        #Carica la foto dal file system
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
            file_data = f.read()
        
        # Carica la foto su S3
        s3.put_object(Bucket=bucket_name, Key=folder_name + filename, Body=file_data)
        
        sendPhoto_to_rabbitmq(filename)
        return filename

@app.route('/images')
def images():
    nomi = []
    files = os.listdir(app.config['EDITED_FOLDER'])
    images = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    #print(','.join(images))
    immagini = ','.join(images)
    nomi = list(app.config['NOMI'])
    return jsonify({'immagini': immagini, 'nomi': nomi})

@app.route('/sendemail/<nome>', methods=['GET', 'POST'])
def send_email(nome):
    #print(nome)
    if request.method == 'POST':
        return redirect("/")
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')







