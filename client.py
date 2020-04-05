from socketIO_client import SocketIO, LoggingNamespace
import time


def room_created(args):
    print('room_created', args)



def my_response(args):
    print("myresponse:",args)

def page_joined(args):
    filepath = 'uploads/input.csv'
    with open(filepath) as fp:
       line = fp.readline()
       cnt = 1
       while line:
           line = fp.readline()
           if len(line) == 0:
               print('empty line')
               break
           socketIO.emit('my event',{'room': args,'message' : line})
           cnt += 1
           time.sleep(.5)
    socketIO.emit('end transfer')
    time.sleep(2)
    socketIO.disconnect()

socketIO = SocketIO('localhost', 5000, LoggingNamespace)
socketIO.on('room_created', room_created)
socketIO.on('page_joined', page_joined)
socketIO.on('my response', my_response)
socketIO.emit('create_room')
socketIO.wait(seconds=20)
