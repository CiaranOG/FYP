from flask import Flask, render_template, request, flash,redirect, url_for,send_from_directory,send_file,Response
from werkzeug.utils import secure_filename
import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime


UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloadables'
ALLOWED_EXTENSIONS = {'csv'}
app = Flask(__name__)
MODEL = pickle.load(open('models/label_spread.sav', 'rb'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

@app.route("/")
def home():
    return render_template("home.html")
@app.route("/run_model_dragdrop")
def run_model_dragdrop():
    return render_template("run_model_drag_drop.html")

@app.route("/predict",methods = ['POST', 'GET'])
def predict():
    if request.method == 'POST':
        result = request.form['nm']
        return render_template("predict.html",result = result)

@app.route("/stream_data")
def stream_data():
    return render_template("stream_data.html")

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
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #return redirect(url_for('uploaded_file', filename='Results.csv'))
            df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            df["GSR Sie"] = df["GSR Sie"].fillna(value=-1)
            df= df.drop(columns=['event'])
            df = df.dropna()
            df= df.drop(columns=['Time', 'GSR kOhm', 'GSR Sie', 'BPM','lookdown time', 'breath rate', 'breath reg', 'height','label'])
            predictions = MODEL.predict(df)
            df['predictions'] = predictions
            # saving the dataframe
            df.to_csv('downloadables/Results.csv',index=False, encoding='utf-8')
            return render_template("run_model.html",dataframe= df, predictions= predictions)
    return render_template("run_model.html",dataframe= None, predictions= None)
from flask import send_from_directory



if __name__ == "__main__":
    app.run(debug=True)
