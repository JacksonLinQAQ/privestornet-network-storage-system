from flask import Flask, render_template, request, redirect, url_for, send_file
from Privestornet.PSNSystem import PSNSystem
from Privestornet.PSNPath import PSNPath
from socket import gethostbyname, gethostname
from jinja2.exceptions import TemplateNotFound
import os, zipfile, shutil

APP_CONFIG = {
    'host': gethostbyname(gethostname()),
    'port': 3000,
    'debug': True,
}

# Create app object
PSN_APP = Flask(__name__)
PSN_SYS = PSNSystem.System()

# Process HTTP requests
@PSN_APP.route('/favicon.ico')
def favicon():
    return send_file('./favicon.ico', mimetype='image/vnd.microsoft.icon')

@PSN_APP.route('/ficon')
def ficon():
    user = request.args.get('user')
    target = request.args.get('target')
    path = request.args.get('path')

    if [request.remote_addr == accessed_user.ip and user == accessed_user.user.username for accessed_user in PSN_SYS.accessed_users]:
        if '.png' in path or '.jpg' in path or '.jpeg' in path:
            if target == 'personal':
                icon = os.path.join(PSNPath.PSNUSERS_USERS_DATA_PATH, user, path)
            elif target == 'public':
                icon = os.path.join(PSNPath.PSNUSERS_PUBLIC_DATA_PATH, path)
            if os.path.exists(icon):
                return send_file(os.path.abspath(icon))
        return 'Unsupported file type'
    return 'Please login first'

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

        # If the user is logged in
        if user.is_login():
            return redirect('./login?page=home')
        
        # If username or password is empty
        if not (request.form['username'] and request.form['password']):
            PSN_SYS.error(request.remote_addr, 'Invaild username or password')
            return redirect(f'./login?error=Invaild%20username%20or%20password')

        status = user.login(request.form['username'], request.form['password'])

        # If the user logs in successfully
        if status[0]:
            PSN_SYS.log(request.remote_addr, f'User \'{user.user.username}\' logged in')
            return redirect('./login?page=home')
        else:
            PSN_SYS.error(request.remote_addr, status[1])
            return redirect(f'./login?error={status[1]}')

    elif request.method == 'GET':
        PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
        user = PSN_SYS.find_user(request.remote_addr)

        # If the user is not logged in
        if not user.is_login():
            return render_template('login/login.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config)

        # Check the page
        page = request.args.get('page')
        if not page:
            return redirect('./login?page=home')

        else:
            try:
                # If the page is not personal or public storage
                if not (page == 'personal' or page == 'public' or page == 'shared-files'):
                    return render_template(f'app/{page}.html', users=PSN_SYS.users, user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config, page=page)

                if page == 'shared-files':
                    PSN_SYS.refresh()
                    data = PSN_SYS.find_user(request.remote_addr).user.received_data
                    return render_template(f'app/{page}.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config, page=page, data=data)

                # If the page is personal or public storage
                # Then check the path
                path = request.args.get('path')

                # Format the path
                if path:
                    path = path.strip('/')
                else:
                    path = ''

                # Set the user current path
                user.path = path

                # Find the data of the path
                if page == 'personal' and user.user.personal_data.quickfind(path=path):
                    data = user.user.personal_data.quickfind(path=path)
                elif page == 'public' and user.user.public_data.quickfind(path=path):
                    data = user.user.public_data.quickfind(path=path)
                else:
                    data = None

                # If the data not exists
                if not data:
                    return render_template(f'error/file-not-found.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config, page=page), 404

                # Check move and receive parameters
                if request.args.get('move') == 'null' or request.args.get('receive') == 'null':
                    return redirect(f'./login?page={page}&path={path}')

                if user.accessed_page[-2][1].get('move') and user.accessed_page[-2][1]['move'] != 'null' and not request.args.get('move'):
                    return redirect(f'./login?page={page}&path={path}&move={user.accessed_page[-2][1]["move"]}')

                if user.accessed_page[-2][1].get('receive') and user.accessed_page[-2][1]['receive'] != 'null' and not request.args.get('receive'):
                    return redirect(f'./login?page={page}&path={path}&receive={user.accessed_page[-2][1]["receive"]}')

                # If the data exists
                # Then check the path type and return it

                if not (data.pathtype == 'root' or data.pathtype == 'folder' or data.pathtype == 'file'):
                    return render_template(f'error/file-not-found.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config, page=page), 404

                if data.pathtype == 'file':
                    # If the user needs to download the data
                    if request.args.get('download'):
                        # Then return it
                        return send_file(os.path.abspath(data.fullpath), as_attachment=True)
                    # Otherwise, just only return the data preview
                    return send_file(os.path.abspath(data.fullpath))

                elif data.pathtype == 'folder':
                    # If the user needs to download the data
                    # Then create a zip file archive and return it
                    if request.args.get('download'):
                        shutil.make_archive(f'./Privestornet/PSNPkgDownload/{os.path.splitext(data.name)[0]}', 'zip', data.fullpath)
                        return send_file(os.path.abspath(f'./Privestornet/PSNPkgDownload/{os.path.splitext(data.name)[0]}.zip'), as_attachment=True)

                # Format the path
                path = path.split('/')
                path_iter = list(enumerate(path))

                # The data has been checked as a folder
                # Return all data of the folder path
                return render_template(f'app/{page}.html', user=PSN_SYS.find_user(request.remote_addr), config=PSN_SYS.config, page=page, data=data, path=path, path_iter=path_iter)
            except TemplateNotFound:
                return redirect('./login?page=home')

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

    # If the user is not logged in
    if not user.is_login():
        return redirect(f'./login')

    username = request.form.get('username')
    confirm_username = request.form.get('confirm-username')

    # If the new username is not the match as the confirm new username
    if not username == confirm_username:
        PSN_SYS.error(request.remote_addr, f'New username \'{username}\' and confirm new username \'{confirm_username}\' do not match')
        return redirect(f'./login?page={request.args.get("page")}&error=New%20username%20and%20confirm%20new%20username%20do%20not%20match')

    # If the new username contains any space characters or it is empty
    if (' ' in username or username == ''):
        PSN_SYS.error(request.remote_addr, f'Invaild username \'{username}\'')
        return redirect(f'./login?page={request.args.get("page")}&error=Invaild%20username%20\'{username}\'')

    # If the new username is the same as the old one
    if username == user.user.username:
        PSN_SYS.error(request.remote_addr, f'The new username \'{username}\' must not be the same as the old username \'{user.user.username}\'')
        return redirect(f'./login?page={request.args.get("page")}&error=The%20new%20username%20must%20not%20be%20the%20same%20as%20the%20old%20username')

    # Otherwise, just change the username
    PSN_SYS.log(request.remote_addr, f'User \'{user.user.username}\' changed username to \'{username}\'')
    user.user.modify_data(username = username)
    return redirect(f'./login?page={request.args.get("page")}&msg=Username%20changed%20to%20\'{username}\'')

@PSN_APP.route('/change-password', methods=['POST'])
def change_password():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    user = PSN_SYS.find_user(request.remote_addr)

    # If the user is not logged in
    if not user.is_login():
        return redirect(f'./login')

    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')

    # If the new password is not the match as the confirm new password
    if not password == confirm_password:
        PSN_SYS.error(request.remote_addr, f'New password \'{password}\' and confirm new password \'{confirm_password}\' do not match')
        return redirect(f'./login?page={request.args.get("page")}&error=New%20password%20and%20confirm%20new%20password%20do%20not%20match')

    # If the new password contains any space characters or it is empty
    if (' ' in password or password == ''):
        PSN_SYS.error(request.remote_addr, f'Invaild password \'{password}\'')
        return redirect(f'./login?page={request.args.get("page")}&error=Invaild%20password%20\'{password}\'')

    # If the new password is the same as the old one
    if password == user.user.password:
        PSN_SYS.error(request.remote_addr, f'The new password \'{password}\' must not be the same as the old password \'{user.user.password}\'')
        return redirect(f'./login?page={request.args.get("page")}&error=The%20new%20password%20must%20not%20be%20the%20same%20as%20the%20old%20password')

    # Otherwise, just change the password
    PSN_SYS.log(request.remote_addr, f'User \'{user.user.password}\' changed password to \'{password}\'')
    user.user.modify_data(password = password)
    return redirect(f'./login?page={request.args.get("page")}&msg=password%20changed%20to%20\'{password}\'')

@PSN_APP.route('/upload', methods=['POST'])
def upload():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    if not PSN_SYS.find_user(request.remote_addr).is_login():
        return redirect(f'./login?page={request.args.get("dst")}&error=Please%20login%20first')

    # Get required parameters
    dst = request.args.get('dst')
    path = request.args.get('path')
    all_data = request.files.getlist('upload-data')
    datatype = request.args.get('type')

    # If the parameters provided are incomplete
    if not (dst and all_data and datatype) or path == None:
        PSN_SYS.error(request.remote_addr, f'Invaild request')
        return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Invaild%20request')

    # If the upload destination is invaild
    if not (dst == 'personal' or dst == 'public'):
        PSN_SYS.error(request.remote_addr, f'Invaild destination \'{dst}\'')
        return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Invaild%20destination%20\'{dst}\'')

    # If the upload path is invaild
    if not (PSN_SYS.find_user(request.remote_addr).user.personal_data.find(path=path) and (PSN_SYS.find_user(request.remote_addr).user.personal_data.find(path=path).pathtype == 'root' or PSN_SYS.find_user(request.remote_addr).user.personal_data.find(path=path).pathtype == 'folder')):
        PSN_SYS.error(request.remote_addr, f'Invaild path \'{path}\'')
        return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Invaild%20path%20\'{path}\'')

    # Otherwise, get the absolute path of the upload path
    if dst == 'personal':
        path = PSN_SYS.find_user(request.remote_addr).user.personal_data.find(path=path).fullpath
    elif dst == 'public':
        path = PSN_SYS.find_user(request.remote_addr).user.public_data.find(path=path).fullpath
    path = os.path.abspath(path)

    unsupported_folders = []

    for data in all_data:
        # If the file in the path
        if data.filename in os.listdir(path):
            PSN_SYS.error(request.remote_addr, f'File \'{data.filename}\' already exists')
            return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=File%20\'{data.filename}\'%20already%20exists')

        # Save file or folder
        data.save(f'{path}/{data.filename}')

        # If data is a folder
        if datatype == 'folder':
            # If the extension of the zip file not correct
            if not os.path.splitext(data.filename)[1] == '.zip':
                unsupported_folders.append(data.filename)

            # If the folder is exists
            if os.path.exists(f'{path}/{os.path.splitext(data.filename)[0]}'):
                # Check if the zip file exists, then delete it
                if os.path.exists(f'{path}/{data.filename}'):
                    os.remove(f'{path}/{data.filename}')   

                PSN_SYS.error(request.remote_addr, f'Folder \'{os.path.splitext(data.filename)[0]}\' already exists')
                return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Folder%20\'{os.path.splitext(data.filename)[0]}\'%20already%20exists')

            # Otherwise, Extract the zip folder
            with zipfile.ZipFile(f'{path}/{data.filename}', 'r') as zip_ref:
                os.makedirs(f'{path}/{os.path.splitext(data.filename)[0]}')

                for member in zip_ref.filelist:
                    try:
                        member.filename = member.filename.encode('cp437').decode('gbk')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        PSN_SYS.error(request.remote_addr, 'Encode or decode file name error occured')
                    zip_ref.extract(member, f'{path}/{os.path.splitext(data.filename)[0]}')

            # Check if the zip file exists, then delete it
            if os.path.exists(f'{path}/{data.filename}'):
                os.remove(f'{path}/{data.filename}')            

    # If there're unsupported folders, then raise error
    if unsupported_folders:
        PSN_SYS.error(request.remote_addr, f'Unsupported folders: \'{", ".join(unsupported_folders)}\'')
        return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&error=Unsupported%20folders:%20\'{",%20".join(unsupported_folders)}\'')

    # Otherwise, return upload success
    PSN_SYS.log(request.remote_addr, f'Upload \'{data.filename}\' to \'{path}\'')
    return redirect(f'./login?page={request.args.get("dst")}&path={request.args.get("path")}&msg=Upload%20success')

@PSN_APP.route('/delete')
def delete():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    if not PSN_SYS.find_user(request.remote_addr).is_login():
        return redirect(f'./login?page={request.args.get("target")}&error=Please%20login%20first')

    # Get required parameters
    path = request.args.get('path')
    target = request.args.get('target')

    # If the parameters provided are incomplete
    if not (path and target):
        PSN_SYS.error(request.remote_addr, f'Invaild request')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20request')

    # Check and find the data
    if target == 'personal':
        data = PSN_SYS.find_user(request.remote_addr).user.personal_data.quickfind(path)
    elif target == 'public':
        data = PSN_SYS.find_user(request.remote_addr).user.public_data.quickfind(path)
    else:
        PSN_SYS.error(request.remote_addr, f'Invaild target \'{target}\'')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20target%20\'{target}\'')

    # If the data not exists
    if not data:
        PSN_SYS.error(request.remote_addr, f'Invaild path \'{path}\'')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20path%20\'{path}\'')

    # Otherwise, remove the data and return the result
    result = data.remove()
    if result[0]:
        PSN_SYS.log(request.remote_addr, f'Deleted \'{path}\' successfully')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&msg=Deleted%20\'{path}\'%20successfully')
    else:
        PSN_SYS.error(request.remote_addr, result[1])
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error={result[1]}')

@PSN_APP.route('/rename', methods=['POST'])
def rename():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    if not PSN_SYS.find_user(request.remote_addr).is_login():
        return redirect(f'./login?page={request.args.get("target")}&error=Please%20login%20first')

    # Get required parameters
    path = request.args.get('path')
    new_name = request.form['new-name']
    target = request.args.get('target')

    # If the parameters provided are incomplete
    if not (path and target and new_name):
        PSN_SYS.error(request.remote_addr, f'Invaild request')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20request')

    # Check and find the data
    if target == 'personal':
        data = PSN_SYS.find_user(request.remote_addr).user.personal_data.quickfind(path)
    elif target == 'public':
        data = PSN_SYS.find_user(request.remote_addr).user.public_data.quickfind(path)
    else:
        PSN_SYS.error(request.remote_addr, f'Invaild target \'{target}\'')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20target%20\'{target}\'')

    # If the data not exists
    if not data:
        PSN_SYS.error(request.remote_addr, f'Invaild path \'{path}\'')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20path%20\'{path}\'')

    # Otherwise, remove the data and return the result
    old_path = data.path
    result = data.rename(new_name)
    if result[0]:
        PSN_SYS.log(request.remote_addr, f'Rename \'{old_path}\' to \'{data.path}\' successfully')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&msg=Rename%20\'{old_path}\'%20to%20\'{data.path}\'%20successfully')
    else:
        PSN_SYS.error(request.remote_addr, result[1])
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error={result[1]}')

@PSN_APP.route('/move')
def move():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    if not PSN_SYS.find_user(request.remote_addr).is_login():
        return redirect(f'./login?page={request.args.get("target")}&error=Please%20login%20first')

    # Get required parameters
    path = request.args.get('path')
    target = request.args.get('target')
    dst = request.args.get('dst')

    # If the parameters provided are incomplete
    if not (path and target and dst != None):
        PSN_SYS.error(request.remote_addr, 'Invaild parameters')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20parameters')

    # Check and find the data
    if target == 'personal':
        data = PSN_SYS.find_user(request.remote_addr).user.personal_data.quickfind(path)
    elif target == 'public':
        data = PSN_SYS.find_user(request.remote_addr).user.public_data.quickfind(path)
    else:
        PSN_SYS.error(request.remote_addr, f'Invaild target \'{target}\'')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20target%20\'{target}\'')

    # If the data not exists
    if not data:
        PSN_SYS.error(request.remote_addr, f'Invaild path \'{path}\'')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20path%20\'{path}\'')

    # Otherwise, move the data to the destination path and return the result
    old_path = data.path
    result = data.move(dst)
    if result[0]:
        PSN_SYS.log(request.remote_addr, f'Move \'{old_path}\' to \'{data.path}\' successfully')
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&msg=Move%20\'{old_path}\'%20to%20\'{data.path}\'%20successfully')
    else:
        PSN_SYS.error(request.remote_addr, result[1])
        return redirect(f'./login?page={request.args.get("target")}&path={"/".join(request.args.get("path").split("/")[:-1])}&error={result[1]}')

@PSN_APP.route('/share', methods=['POST'])
def share():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    if not PSN_SYS.find_user(request.remote_addr).is_login():
        return redirect(f'./login?page={request.args.get("target")}&error=Please%20login%20first')

    # Get required parameters
    path = request.args.get('path')
    share_to = request.form['share-to']

    # If the parameters provided are incomplete
    if not (path and share_to):
        PSN_SYS.error(request.remote_addr, 'Invaild parameters')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20parameters')

    # Check and find the data
    data = PSN_SYS.find_user(request.remote_addr).user.personal_data.quickfind(path)

    # If the data not exists
    if not data:
        PSN_SYS.error(request.remote_addr, f'Invaild path \'{path}\'')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20path%20\'{path}\'')

    # Check that the file or folder was sent by and shared with this user
    if data.username == share_to:
        PSN_SYS.error(request.remote_addr, f'Cannot share with yourself')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Cannot%20share%20with%20yourself')

    # If the user not exists
    if not PSN_SYS.users.find_user(share_to):
        PSN_SYS.error(request.remote_addr, f'User \'{share_to}\' does not exist')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error=User%20\'{share_to}\'%20does%20not%20exist')

    # Otherwise, send the data to the user and return the result
    result = PSN_SYS.find_user(request.remote_addr).user.share_data(share_to, data)
    if result[0]:
        PSN_SYS.users.load_users()
        PSN_SYS.log(request.remote_addr, f'User \'{PSN_SYS.find_user(request.remote_addr).user.username}\' shared \'{data.path}\' to user \'{share_to}\' successfully')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&msg=Shared%20\'{data.path}\'%20to%20user%20\'{share_to}\'%20successfully')
    else:
        PSN_SYS.error(request.remote_addr, result[1])
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error={result[1]}')

@PSN_APP.route('/accept')
def accept():
    PSN_SYS.access(request.remote_addr, request.path, dict(request.args))
    if not PSN_SYS.find_user(request.remote_addr).is_login():
        return redirect(f'./login?page={request.args.get("from-user")}&error=Please%20login%20first')

    # Get required parameters
    path = request.args.get('path')
    data = request.args.get('data')

    # If the parameters provided are incomplete
    if not (path != None and data):
        PSN_SYS.error(request.remote_addr, 'Invaild parameters')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invaild%20parameters')

    # Check and find the data
    data = [ shared_file for shared_file in PSN_SYS.find_user(request.remote_addr).user.received_data if shared_file.sent_data.name == data ]
    if data:
        data = data[0]
    else:
        PSN_SYS.error(request.remote_addr, 'Shared file or folder not found')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Shared%20file%20or%20folder%20not%20found')

    # Check the save path
    path = PSN_SYS.find_user(request.remote_addr).user.personal_data.quickfind(path)
    if not (path and (path.pathtype == 'folder' or path.pathtype == 'root')):
        PSN_SYS.error(request.remote_addr, 'Invalid save path')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error=Invalid%20save%20path')

    # Accept the shared file or folder
    result = data.accept(path)
    if result[0]:
        PSN_SYS.users.load_users()
        PSN_SYS.log(request.remote_addr, f'User \'{PSN_SYS.find_user(request.remote_addr).user.username}\' received \'{data.sent_data.path}\' from \'{data.sent_from}\' successfully')
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&msg=Received%20\'{data.sent_data.path}\'%20from%20\'{data.sent_from}\'%20successfully')
    else:
        PSN_SYS.error(request.remote_addr, result[1])
        return redirect(f'./login?page=personal&path={"/".join(request.args.get("path").split("/")[:-1])}&error={result[1]}')