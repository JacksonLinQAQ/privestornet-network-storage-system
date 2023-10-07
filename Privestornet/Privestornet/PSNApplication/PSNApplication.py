from flask import Flask, render_template, request, redirect, url_for, send_file
from Privestornet.PSNSystem import PSNSystem
from socket import gethostbyname, gethostname
from jinja2.exceptions import TemplateNotFound
import os, zipfile

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
                    if page == 'personal' or page == 'public':
                        path = request.args.get('path')
                        if path:
                            path = path.strip('/')
                        else:
                            path = ''
                        user.path = path

                        if page == 'personal' and user.user.personal_data.quickfind(path=path):
                            data = user.user.personal_data.quickfind(path=path)
                        elif page == 'public' and user.user.public_data.quickfind(path=path):
                            data = user.user.public_data.quickfind(path=path)
                        else:
                            data = None

                        if data.pathtype == 'file':
                            if request.args.get('download'):
                                return send_file(os.path.abspath(data.fullpath), as_attachment=True)
                            else:
                                return send_file(os.path.abspath(data.fullpath))

                        path = path.split('/')
                        path_iter = list(enumerate(path))
                    else:
                        path = None
                        path_iter = None
                        data = None
                    return render_template(f'app/{page}.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config, page=page, path=path, path_iter=path_iter, data=data)
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

@PSN_APP.route('/change-username', methods=['POST'])
def change_username():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    user = PSN_SYS.find_user(request.remote_addr)
    # If the user is logged in
    if user.is_login():
        username = request.form.get('username')
        confirm_username = request.form.get('confirm-username')

        # If the new username is the same as the confirm new username
        if username == confirm_username:
            # If the new username doesn't contain any space characters
            if not ' ' in username:
                # If the new username isn't the same as the old one
                if not username == user.user.username:
                    PSN_SYS.log(request.remote_addr, f'User \'{user.user.username}\' changed username to \'{username}\'')
                    user.user.modify_data(username = username)
                    return redirect(f'./login?page={request.args.get("page")}&msg=Username%20changed%20to%20\'{username}\'')

                PSN_SYS.error(request.remote_addr, f'The new username \'{username}\' must not be the same as the old username \'{user.user.username}\'')
                return redirect(f'./login?page={request.args.get("page")}&error=The%20new%20username%20must%20not%20be%20the%20same%20as%20the%20old%20username')

            PSN_SYS.error(request.remote_addr, f'Invaild username \'{username}\'')
            return redirect(f'./login?page={request.args.get("page")}&error=Invaild%20username%20\'{username}\'')

        PSN_SYS.error(request.remote_addr, f'New username \'{username}\' and confirm new username \'{confirm_username}\' do not match')
        return redirect(f'./login?page={request.args.get("page")}&error=New%20username%20and%20confirm%20new%20username%20do%20not%20match')

    return redirect(f'./login')

@PSN_APP.route('/change-password', methods=['POST'])
def change_password():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    user = PSN_SYS.find_user(request.remote_addr)
    # If the user is logged in
    if user.is_login():
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        # If the new password is the same as the confirm new password
        if password == confirm_password:
            # If the new password doesn't contain any space characters
            if not ' ' in password:
                # If the new password isn't the same as the old one
                if not password == user.user.password:
                    PSN_SYS.log(request.remote_addr, f'User \'{user.user.password}\' changed password to \'{password}\'')
                    user.user.modify_data(password = password)
                    return redirect(f'./login?page={request.args.get("page")}&msg=password%20changed%20to%20\'{password}\'')

                PSN_SYS.error(request.remote_addr, f'The new password \'{password}\' must not be the same as the old password \'{user.user.password}\'')
                return redirect(f'./login?page={request.args.get("page")}&error=The%20new%20password%20must%20not%20be%20the%20same%20as%20the%20old%20password')

            PSN_SYS.error(request.remote_addr, f'Invaild password \'{password}\'')
            return redirect(f'./login?page={request.args.get("page")}&error=Invaild%20password%20\'{password}\'')

        PSN_SYS.error(request.remote_addr, f'New password \'{password}\' and confirm new password \'{confirm_password}\' do not match')
        return redirect(f'./login?page={request.args.get("page")}&error=New%20password%20and%20confirm%20new%20password%20do%20not%20match')

    return redirect(f'./login')

@PSN_APP.route('/upload', methods=['POST'])
def upload():
    if not PSN_SYS.find_user(request.remote_addr).is_login():
        return redirect(f'./login?page={request.args.get("dst")}&error=Please%20login%20first')

    dst = request.args.get('dst')
    path = request.args.get('path')
    all_data = request.files.getlist('upload-data')
    datatype = request.args.get('type')

    if not dst or path == None or not all_data or not datatype:
        PSN_SYS.error(request.remote_addr, f'Invaild request')
        return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Invaild%20request')

    if not (dst == 'personal' or dst == 'public'):
        PSN_SYS.error(request.remote_addr, f'Invaild destination \'{dst}\'')
        return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Invaild%20destination%20\'{dst}\'')

    if not (PSN_SYS.find_user(request.remote_addr).user.personal_data.find(path=path).pathtype == 'root' or PSN_SYS.find_user(request.remote_addr).user.personal_data.find(path=path).pathtype == 'folder'):
        PSN_SYS.error(request.remote_addr, f'Invaild path \'{path}\'')
        return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Invaild%20path%20\'{path}\'')

    # Get absolute path
    if dst == 'personal':
        path = PSN_SYS.find_user(request.remote_addr).user.personal_data.find(path=path).fullpath
    elif dst == 'public':
        path = PSN_SYS.find_user(request.remote_addr).user.public_data.find(path=path).fullpath
    path = os.path.abspath(path)

    for data in all_data:
        # Save file or folder
        data.save(f'{path}/{data.filename}')

        # Check if data is a folder
        if datatype == 'folder':
            # Extract the zip folder
            with zipfile.ZipFile(f'{path}/{data.filename}', 'r', metadata_encoding='utf-8') as zip_ref:
                os.makedirs(f'{path}/{os.path.splitext(data.filename)[0]}')
                zip_ref.extractall(f'{path}/{os.path.splitext(data.filename)[0]}')

            # Check if the zip file exists, then delete it
            if os.path.exists(f'{path}/{data.filename}'):
                os.remove(f'{path}/{data.filename}')

    PSN_SYS.log(request.remote_addr, f'Upload \'{data.filename}\' to \'{path}\'')
    return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&msg=Upload%20success')