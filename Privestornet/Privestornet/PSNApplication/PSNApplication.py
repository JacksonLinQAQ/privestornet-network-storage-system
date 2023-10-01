from flask import Flask, render_template, request, redirect, url_for, send_file
from Privestornet.PSNSystem import PSNSystem
from socket import gethostbyname, gethostname

APP_CONFIG = {
    'host': gethostbyname(gethostname()),
    'port': 3000,
    'debug': True,
}

# Create app object
PSN_APP = Flask(__name__)
PSN_SYS = PSNSystem.System()

# Process HTTP requests
@PSN_APP.route('/')
@PSN_APP.route('/index')
def index():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    return render_template('index/index.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config)

@PSN_APP.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
        pass
    elif request.method == 'GET':
        return render_template('login/login.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config)