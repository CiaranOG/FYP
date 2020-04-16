from flask import Flask, render_template, request, flash,redirect, url_for,send_from_directory,send_file,Response
from werkzeug.utils import secure_filename
import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room
import json
from flask_session import Session
import random

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloadables'
ALLOWED_EXTENSIONS = {'csv'}
app = Flask(__name__)
MODEL = pickle.load(open('models/SVM.sav', 'rb'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
Session(app)
socketio = SocketIO(app) #, manage_session=False
ROOMS = []
@app.route("/")
def home():
    return render_template("home.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/downloadables/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'],
                               filename)

@app.route('/run_model', methods=['GET', 'POST'])
def run_model():
    if request.method == 'POST':
        try:
            # check if the post request has the file part
            if 'file' not in request.files:
                raise ValueError('No file part')
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                raise ValueError('No file selected')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                #return redirect(url_for('uploaded_file', filename='Results.csv'))
                df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                df = df.dropna()
                df= df[['delta', 'alpha1', 'alpha2', 'beta1', 'beta2', 'theta', 'gamma1','gamma2']]
                predictions = MODEL.predict(df)
                df['predictions'] = predictions
                # saving the dataframe
                df.to_csv('downloadables/Results.csv',index=False, encoding='utf-8')
                return render_template("run_model.html",dataframe= df, predictions= predictions, error= None)
        except ValueError as e:
            return render_template("run_model.html",dataframe= None, predictions= None, error= e)
        except:
            e = "Error converting to dataframe and running model make sure file is .csv and has columns 'delta', 'alpha1', 'alpha2', 'beta1', 'beta2', 'theta', 'gamma1','gamma2'"
            return render_template("run_model.html",dataframe= None, predictions= None, error= e)
    return render_template("run_model.html",dataframe= None, predictions= None, error= None)
from flask import send_from_directory

@app.route('/enter_room', methods=['GET', 'POST'])
def enter_room():
    global ROOMS
    if request.method == 'POST':
        try:
            if len(request.form.get('code')) == 0 :
                raise ValueError('No code entered')
            if int(request.form.get('code')) not in ROOMS:
                raise ValueError('No room exists with code "{}".'.format(request.form.get('code')))
            if int(request.form.get('code')) in ROOMS:
                roomURL = "room/" + str(request.form.get('code'))
                return redirect(roomURL)
        except ValueError as e:
            return render_template("enter_room.html", error = e)
        except:
            return render_template("enter_room.html", error = e)
    return render_template("enter_room.html")

@app.route('/room/<room>')
def show_room(room):
    global ROOMS
    if int(room) in ROOMS:
        return render_template("room.html", room_code = room)
    else:
        return render_template("room.html",room_code = None )

@app.route("/stream_data")
def stream_data():
    return render_template("stream_data.html")

@socketio.on('end transfer')
def end_transfer():
    socketio.emit('end transfer', broadcast=True)

@socketio.on('Webpage_enter_room')
def Webpage_enter_room(room_code):
    join_room(room_code)
    socketio.emit("page_joined",str(room_code), room=room_code)
    return

@socketio.on('create_room')
def create_room():
    print(request.sid)
    global ROOMS
    room_assigned= False
    while not room_assigned:
        code = random.randint(1000, 9999)
        if code not in ROOMS:
            join_room(code)
            ROOMS += [code]
            print("Here:",ROOMS)
            socketio.emit('room_created', code,room=request.sid)
            print('sending message "{}" to room "{}".'.format(code, request.sid))
            room_assigned = True




@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    try:
        line = json['message']
        line = line.replace(",,",", -1,")
        line = line.replace(",0,",", -1,")
        line = line.strip('\n')
        df = pd.DataFrame(eval(line))
        prediction =  MODEL.predict(df.transpose())
        json['message'] = line + ", " + str(prediction[0])
        f = open("downloadables/report.csv", "a")
        f.write(line + ", " + str(prediction[0]) + "\n")
        f.close()
        socketio.emit('my response', json, room = int(json['room']) )
    except:
        socketio.emit('Stream failed', room = int(json['room']) )


if __name__ == "__main__":
    socketio.run(app,debug=True)
