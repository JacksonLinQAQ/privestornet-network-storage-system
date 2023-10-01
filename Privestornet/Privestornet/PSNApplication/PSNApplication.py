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
        user = PSN_SYS.find_user(request.remote_addr)
        if not user.is_login():
            if request.form['username'] and request.form['password']:
                status = user.login(request.form['username'], request.form['password'])
                if status[0]:
                    return redirect('./login')
                else:
                    return redirect(f'./login?error={status[1]}')
            return redirect(f'./login?error=Invaild%20username%20and%20password')
        return redirect('./login')

    elif request.method == 'GET':
        PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
        user = PSN_SYS.find_user(request.remote_addr)
        if user.is_login():
            return render_template('app/home.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config)
        return render_template('login/login.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config)

@PSN_APP.route('/logout')
def logout():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    user = PSN_SYS.find_user(request.remote_addr)
    username = user.user.username
    if user.is_login():
        user.logout()
    return redirect(f'./login?msg=User%20\'{username}\'%20logged%20out')