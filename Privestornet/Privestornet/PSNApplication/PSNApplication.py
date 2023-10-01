from flask import Flask, render_template, request, redirect, url_for, send_file
from Privestornet.PSNSystem import PSNSystem
from socket import gethostbyname, gethostname
from jinja2.exceptions import TemplateNotFound

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

        # If the user is not logged in yet
        if not user.is_login():
            # If username and password is not empty
            if request.form['username'] and request.form['password']:
                status = user.login(request.form['username'], request.form['password'])
                # If the user logs in successfully
                if status[0]:
                    PSN_SYS.log(request.remote_addr, f'User \'{user.user.username}\' logged in')
                    return redirect('./login?page=home')
                else:
                    PSN_SYS.error(request.remote_addr, status[1])
                    return redirect(f'./login?error={status[1]}')
            PSN_SYS.error(request.remote_addr, 'Invaild username or password')
            return redirect(f'./login?error=Invaild%20username%20or%20password')
        return redirect('./login?page=home')

    elif request.method == 'GET':
        PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
        user = PSN_SYS.find_user(request.remote_addr)
        # If the user is logged in
        if user.is_login():
            page = request.args.get('page')
            if not page:
                return redirect('./login?page=home')
            else:
                try:
                    return render_template(f'app/{page}.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config)
                except TemplateNotFound:
                    return redirect('./login?page=home')
        return render_template('login/login.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config)

@PSN_APP.route('/logout')
def logout():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    user = PSN_SYS.find_user(request.remote_addr)
    username = user.user.username
    # If the user is logged in
    if user.is_login():
        user.logout()
    PSN_SYS.log(request.remote_addr, f'User \'{username}\' logged out')
    return redirect(f'./login?msg=User%20\'{username}\'%20logged%20out')