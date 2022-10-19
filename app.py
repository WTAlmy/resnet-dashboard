"""Main app file for the dashboard."""
import os
import json

from flask import Flask, render_template
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler

from _itr import high_priority, get_tickets_meta

app = Flask(__name__)  # Flask instance
socketio = SocketIO(app)  # Using Flask SocketIO

num_tickets = 0

def itr():
    """Emit ITR ticket data."""
    global num_tickets

    print('[ITR]: Running... ')
    data_itr = high_priority()
    print('[ITR]: {} tickets'.format(len(data_itr['tickets'])))

    if int(num_tickets) < len(data_itr['tickets']):
        os.system('mpg123 sounds/new_ticket.mp3 &')
    elif int(num_tickets) > len(data_itr['tickets']):
        os.system('mpg123 sounds/done_ticket.mp3 &')
    num_tickets = len(data_itr['tickets'])
    socketio.emit('itr', data_itr, broadcast=True, json=True)

    meta = get_tickets_meta()
    socketio.emit('meta', meta, broadcast=True, json=True)


"""Job Scheduling"""
scheduler = BackgroundScheduler()
# configure each job (how often it runs)
scheduler.add_job(itr, 'interval', seconds=5, max_instances=1)


@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Render Dashboard redirect function."""
    scheduler.start()
    return render_template('dashboard.html')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
