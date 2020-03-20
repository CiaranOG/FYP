import socketio
import time

def on_aaa_response(args):
    print('on_aaa_response', args['data'])

socketIO = socketio.Client()
socketIO.connect('http://localhost:5000')
filepath = 'uploads/input.csv'
with open(filepath) as fp:
   line = fp.readline()
   cnt = 1
   while line:
       line = fp.readline()
       socketIO.emit('my event',{'user_name': 'client','message' : line})
       cnt += 1
       time.sleep(.5)
socketIO.emit('end transfer')
time.sleep(2)
socketIO.disconnect()
