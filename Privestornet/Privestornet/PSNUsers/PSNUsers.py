# <-- PSNUsers --> #

# Required modules
import os, sys, shutil, json, datetime
from typing import TypeAlias, Literal
from Privestornet.PSNPath.PSNPath import PSNUSERS_USERS_DATA_PATH, PSNUSERS_PUBLIC_DATA_PATH, PSNUSERS_USERS_CONFIG_PATH

# Define data types
PATHSOURCE: TypeAlias = Literal['personal', 'public']
PATHTYPE: TypeAlias = Literal['root', 'folder', 'file']

# Concatenate path function
def concatpath(*args):
    return os.path.join(*args).replace('\\', '/').strip('/')

# Path object
class Path:
    def __init__(self, pathsource: PATHSOURCE, pathtype: PATHTYPE, path: str, name: str = None, username: str = None):
        '''
            Path object allows to access users or public data
        '''
        # Create a new Path object
        # Save all the information of the user path
        self.pathsource = pathsource
        self.pathtype = pathtype
        self.name = name
        self.path = path
        self.fullpath = None
        self.content: list['Path'] = [] if self.pathtype == 'root' or self.pathtype == 'folder' else None
        self.content_dict: dict[str, 'Path'] = {} if self.pathtype == 'root' or self.pathtype == 'folder' else None
        self.username = username if self.pathsource == 'personal' else None

        # Run self-check process
        self.self_check_status = self.__self_check()
        if not self.self_check_status[0]:
            raise Exception(self.self_check_status[1])

        # Scan content
        self.scan_content()

    def __self_check(self):
        # Check if the path exists
        if self.pathsource == 'personal':
            self.__root_path = concatpath(PSNUSERS_USERS_DATA_PATH, self.username)
        elif self.pathsource == 'public':
            self.__root_path = PSNUSERS_PUBLIC_DATA_PATH
        else:
            return False, 'Unknown path source'

        if not os.path.isdir(self.__root_path):
            return False, f'User or public \'{self.username if self.pathsource == "personal" else "public"}\' not exists'

        self.fullpath = concatpath(self.__root_path, self.path)
        if not os.path.exists(self.fullpath):
            return False, f'Path \'{self.fullpath}\' does not exist'

        # Check if the file or directory name and path type match
        if self.pathtype != 'root':
            if not os.path.split(self.fullpath)[1] == self.name:
                return False, f'File or directory name \'{self.name}\' does not match'

        if os.path.isfile(self.fullpath):
            if not self.pathtype == 'file':
                return False, f'Path type \'{self.pathtype}\' does not match'
        elif os.path.isdir(self.fullpath):
            if not (self.pathtype == 'root' or self.pathtype == 'folder'):
                return False, f'Path type \'{self.pathtype}\' does not match'

        return True, 'OK'

    def scan_content(self):
        '''
            Scan and save each file or directory as Path object
        '''
        if self.pathtype == 'root' or self.pathtype == 'folder':
            # Clear the old content data
            self.content.clear()
            self.content_dict.clear()

            # Scan and save each file or directory as Path object
            for f in os.listdir(self.fullpath):
                if os.path.isdir(concatpath(self.fullpath, f)):
                    self.content.append(PersonalFolder(concatpath(self.path, f), self.username, f) if self.pathsource == 'personal' else PublicFolder(concatpath(self.path, f), f))
                    self.content_dict.update({f: self.content[-1]})
                elif os.path.isfile(concatpath(self.fullpath, f)):
                    self.content.append(PersonalFile(concatpath(self.path, f), self.username, f) if self.pathsource == 'personal' else PublicFile(concatpath(self.path, f), f))
                    self.content_dict.update({f: self.content[-1]})

            return (True, self.content)
        
        return (False, 'Scan content function only for root or folder')

    def _update_subfiles_location(self):
        self.scan_content()
        if self.pathtype == 'folder':
            for c in self.content:
                c.path = concatpath(self.path, c.name)
                c.fullpath = concatpath(self.fullpath, c.name)

                if c.pathtype == 'folder':
                    c._update_subfiles_location()

                return (True, 'OK')
        else:
            return (False, 'Update subfiles location function only for folder')

    def rename(self, new_name: str):
        '''
            Rename the file or folder
        '''
        self.scan_content()
        if self.pathtype != 'root':
            old_name = self.name
            location = os.path.split(self.path)[0]
            full_location = os.path.split(self.fullpath)[0]

            # Check if the new name already exists
            if not os.path.exists(concatpath(full_location, new_name)):
                # If the new name does not exists
                # Rename the file or folder
                os.rename(self.fullpath, concatpath(full_location, new_name))

                # Update information
                self.name = new_name
                self.path = concatpath(location, new_name)
                self.fullpath = concatpath(full_location, new_name)
                self._update_subfiles_location()

                # Remove the old file or folder if it still exists
                if os.path.exists(concatpath(full_location, old_name)):
                    if self.pathtype == 'folder':
                        shutil.rmtree(concatpath(full_location, old_name))
                    elif self.pathtype == 'file':
                        os.remove(concatpath(full_location, old_name))

                return (True, 'OK')

            return (False, f'Path \'{concatpath(full_location, new_name)}\' already exists')

        return (False, 'Rename function only for file or folder')

    def remove(self):
        '''
            Remove the file or folder
        '''
        self.scan_content()
        if self.pathtype == 'folder':
            shutil.rmtree(self.fullpath)
            return (True, 'OK')
        elif self.pathtype == 'file':
            os.remove(self.fullpath)
            return (True, 'OK')
        else:
            return (False, 'Remove function only for file or folder')

    def move(self, location: str):
        '''
            Move the file or folder to a new location
        '''
        self.scan_content()
        if self.pathtype != 'root':
            # Find the object of the location
            if self.pathsource == 'personal':
                if location == '':
                    location_obj = PersonalRoot(self.username)
                else:
                    location_obj = PersonalFolder(location, self.username, os.path.split(location)[1])

            elif self.pathsource == 'public':
                if location == '':
                    location_obj = PublicRoot()
                else:
                    location_obj = PublicFolder(location, os.path.split(location)[1])

            else:
                return (False, 'Move function only for a root or folder location of personal or public')

            # If the file or folder in the destination location
            if self.name in [c.name for c in location_obj.content_dict.values()]:
                return (False, f'Path \'{concatpath(location_obj.path, self.name)}\' already exists')

            # Move the file or folder to the location
            shutil.move(self.fullpath, concatpath(location_obj.fullpath, self.name))

            # Remove the old file or folder if it still exists
            if self.pathtype == 'folder' and os.path.isdir(self.fullpath):
                shutil.rmtree(self.fullpath)
            elif self.pathtype == 'file' and os.path.isfile(self.fullpath):
                os.remove(self.fullpath)

            # Update new path
            self.path = concatpath(location_obj.path, self.name)
            self.fullpath = concatpath(location_obj.fullpath, self.name)
            self._update_subfiles_location()
            self.scan_content()

            return (True, 'OK')

        return (False, 'Move function only for file or folder')

    def quickfind(self, path: str):
        '''
            Find a file or folder by path quickly
        '''
        self.scan_content()
        if self.pathtype == 'root':
            path = path.split('/')
            data: Path = None

            if path[0] == '':
                return self

            for p in path:
                if data:
                    data = data.content_dict.get(p)
                    if not data:
                        return None
                else:
                    data = self.content_dict.get(p)
                    if not data:
                        return None

                if not data:
                    return None

            return data

    def find(self, name: str = None, path: str = None):
        '''
            Find a file or folder by name or path
        '''
        self.scan_content()

        if name != None:
            if self.pathtype == 'root' or self.pathtype == 'folder':
                for c in self.content:
                    if name == c.name:
                        return c

        if path != None:
            if path == self.path:
                return self
            elif self.pathtype == 'root' or self.pathtype == 'folder':
                for c in self.content:
                    if c.find(path=path):
                        return c.find(path=path)

    def create_file(self, name: str, content: str = ''):
        '''
            Create a new file at this location
        '''
        self.scan_content()
        if self.pathtype == 'root' or self.pathtype == 'folder':
            filefullpath = concatpath(self.fullpath, name)
            # Check if the file does not exist
            if not os.path.exists(filefullpath):
                with open(filefullpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.scan_content()
                return (True, 'OK')
            return (False, f'File \'{filefullpath}\' already exists')
        return (False, 'Create file function only for root or folder')

    def create_folder(self, name: str):
        '''
            Create a new folder at this location
        '''
        self.scan_content()
        if self.pathtype == 'root' or self.pathtype == 'folder':
            folderfullpath = concatpath(self.fullpath, name)
            # Check if the file does not exist
            if not os.path.exists(folderfullpath):
                os.makedirs(folderfullpath)
                self.scan_content()
                return (True, 'OK')
            return (False, f'File \'{folderfullpath}\' already exists')
        return (False, 'Create folder function only for root or folder')

    def clear(self):
        '''
            Clear all contents of this root or folder
        '''
        self.scan_content()
        if self.pathtype == 'root' or self.pathtype == 'folder':
            for c in self.content:
                c.remove()
            return (True, 'OK')
        return (False, 'Clear function only for root or folder')

    def show_map(self):
        '''
            Print out the map of the path data list
        '''
        data = self.to_dict()
        print(json.dumps(data, indent=4))

    def to_dict(self):
        '''
            Convert the path object to a dictionary
        '''
        self.scan_content()
        if self.pathtype == 'root':
            return {
                'pathsource': self.pathsource,
                'pathtype': self.pathtype,
                'username': self.username,
                'name': self.name,
                'path': self.path,
                'fullpath': self.fullpath,
                'content': { c.name: c.to_dict() for c in self.content }
            }
        elif self.pathtype == 'folder':
            return {
                'pathsource': self.pathsource,
                'pathtype': self.pathtype,
                'username': self.username,
                'name': self.name,
                'path': self.path,
                'fullpath': self.fullpath,
                'content': { c.name: c.to_dict() for c in self.content }
            }
        elif self.pathtype == 'file':
            return {
                'pathsource': self.pathsource,
                'pathtype': self.pathtype,
                'username': self.username,
                'name': self.name,
                'path': self.path,
                'fullpath': self.fullpath,
                'content': None
            }

# Personal path objects
class PersonalRoot(Path):
    def __init__(self, username: str):
        super().__init__('personal', 'root', '', None, username)

class PersonalFolder(Path):
    def __init__(self, path: str, username: str, name: str):
        super().__init__('personal', 'folder', path, name, username)

class PersonalFile(Path):
    def __init__(self, path: str, username: str, name: str):
        super().__init__('personal', 'file', path, name, username)

# Public path objects
class PublicRoot(Path):
    def __init__(self):
        super().__init__('public', 'root', '', None, None)

class PublicFolder(Path):
    def __init__(self, path: str, name: str):
        super().__init__('public', 'folder', path, name, None)

class PublicFile(Path):
    def __init__(self, path: str, name: str):
        super().__init__('public', 'file', path, name, None)

# Shared data object
class SharedData:
    def __init__(self, users: 'Users', sent_from: str, send_to: str, send_data: Path, sent_date: str = datetime.datetime.now().strftime(r'%Y-%m-%d %H:%M:%S')):
        self.users = users
        self.sent_from = sent_from
        self.sent_to = send_to
        self.sent_data = send_data
        self.sent_date = sent_date

    def accept(self, save_path: Path = None):
        '''
            Accept and save received data
            - If save_path is None, the save_path will set to '' by default
        '''

        if not save_path:
            save_path = PersonalRoot(self.sent_to)

        if save_path.pathtype == 'file':
            return (False, 'Unsupported save path type \'file\'')

        if save_path.find(self.sent_data.name):
            return (False, f'File or folder \'{self.sent_data.name}\' already exists')

        save_path = concatpath(save_path.fullpath, self.sent_data.name)

        if self.sent_data.pathtype == 'folder':
            # Copy the folder from the shared path
            shutil.copytree(self.sent_data.fullpath, save_path)

            # Delete the shared record if it exists
            if self in self.users.find_user(self.sent_to).received_data:
                self.users.find_user(self.sent_to).received_data.remove(self)
                self.users.save_users()

            return (True, 'OK')
        elif self.sent_data.pathtype == 'file':
            # Copy the file from the shared path
            shutil.copyfile(self.sent_data.fullpath, save_path)

            # Delete the shared record if it exists
            if self in self.users.find_user(self.sent_to).received_data:
                self.users.find_user(self.sent_to).received_data.remove(self)
                self.users.save_users()

            return (True, 'OK')
        return (False, 'Unsupported path type')

    def to_dict(self):
        return {
            'sent-from': self.sent_from,
            'sent-to': self.sent_to,
            'sent-data': self.sent_data.to_dict(),
            'sent-date': self.sent_date
        }

# User object
class User:
    def __init__(self, users: 'Users', username: str, password: str, is_administrator: bool = False, received_data: list[SharedData] = []):
        self._self_check_status = None
        self.users = users
        self.username = username
        self.password = password
        self.is_administrator = is_administrator
        self.received_data: list[SharedData] = received_data

    def _self_check(self):
        for user in self.users.users:
            # Check if the user is exists
            if user.username == self.username:
                # Check if the user data are match
                if user.password == self.password and user.is_administrator == self.is_administrator:
                    self.personal_data = PersonalRoot(self.username)
                    self.public_data = PublicRoot()
                    return (True, 'OK')
                else:
                    return (False, f'User \'{self.username}\' data not match')
        else:
            return (False, f'User \'{self.username}\' does not exist')

    def modify_data(self, username: str = None, password: str = None, is_administrator: bool = None):
        '''
            Modify user data
        '''
        # Check if the new username does not exists
        if username and (not os.path.exists(concatpath(PSNUSERS_USERS_DATA_PATH, username))):
            old_username = self.username
            self.username = username
            shutil.move(concatpath(PSNUSERS_USERS_DATA_PATH, old_username), concatpath(PSNUSERS_USERS_DATA_PATH, self.username))
            if os.path.exists(concatpath(PSNUSERS_USERS_DATA_PATH, old_username)):
                shutil.rmtree(concatpath(PSNUSERS_USERS_DATA_PATH, old_username))
            self.personal_data = PersonalRoot(self.username)
        if password:
            self.password = password
        if is_administrator:
            self.is_administrator = is_administrator
        self.users.save_users()
        return (True, 'OK')

    def remove_user(self):
        '''
            Remove user
        '''
        if os.path.exists(concatpath(PSNUSERS_USERS_DATA_PATH, self.username)):
            shutil.rmtree(concatpath(PSNUSERS_USERS_DATA_PATH, self.username))
        if self in self.users.users:
            self.users.users.remove(self)
        return self.users.users

    def share_data(self, send_to: str, send_data: Path):
        '''
            Share file or folder to other user
        '''
        if self.personal_data.find(path = send_data.path):
            if self.personal_data.find(path = send_data.path).pathtype != 'root':
                self.users.find_user(send_to).received_data.append(SharedData(
                    self.users,
                    self.username,
                    send_to,
                    send_data
                ))
                self.users.save_users()
                return (True, 'OK')
            return (False, f'Cannot share root data')
        return (False, f'File or folder \'{send_data.path}\' not exists')

    def to_dict(self, show_detail = True):
        '''
            Convert the user object to a dictionary
        '''
        if self._self_check_status:
            if show_detail:
                return {
                    'username': self.username,
                    'password': self.password,
                    'is-administrator': self.is_administrator,
                    'received-data': [data.to_dict() for data in self.received_data],
                    'personal-data': self.personal_data.to_dict(),
                    'public-data': self.public_data.to_dict()
                }
            else:
                return {
                    'username': self.username,
                    'password': self.password,
                    'is-administrator': self.is_administrator,
                    'received-data': [data.to_dict() for data in self.received_data]
                }

# Users object
class Users:
    SAVE_USERS_KEEP_DETAIL = True
    def __init__(self):
        self.users: list[User] = []
        self.load_users()

    def load_users(self):
        '''
            Load all users
        '''
        self.users = []
        with open(PSNUSERS_USERS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            for user in users_data['users']:
                user = users_data['users'][user]
                self.users.append(User(
                    self,
                    user['username'],
                    user['password'],
                    user['is-administrator'],
                    [
                        SharedData(
                            self,
                            data['sent-from'],
                            data['sent-to'],
                            PersonalFolder(
                                data['sent-data']['path'],
                                data['sent-data']['username'],
                                data['sent-data']['name']
                            ) if data['sent-data']['pathtype'] == 'folder' else 
                            PersonalFile(
                                data['sent-data']['path'],
                                data['sent-data']['username'],
                                data['sent-data']['name']
                            ),
                            data['sent-date']
                        ) for data in user['received-data'] if os.path.exists(data['sent-data']['fullpath'])
                    ]
                ))

                self.users[-1]._self_check_status = self.users[-1]._self_check()
                if not self.users[-1]._self_check_status[0]:
                    raise Exception(self.users[-1]._self_check_status[1])

    def create_user(self, username: str, password: str, is_administrator: bool = False):
        '''
            Create a new user
        '''

        # Check if user does not exist
        if username not in self.list_usernames():
            os.makedirs(concatpath(PSNUSERS_USERS_DATA_PATH, username))
            self.users.append(User(
                self,
                username,
                password,
                is_administrator,
                []
            ))

            self.users[-1]._self_check_status = self.users[-1]._self_check()
            if not self.users[-1]._self_check_status[0]:
                raise Exception(self.users[-1]._self_check_status[1])

            self.save_users()

            return (True, 'OK')
        return (False, f'User \'{username}\' already exists')

    def find_user(self, username: str):
        '''
            Get user by username
        '''
        for user in self.users:
            if user.username == username:
                return user

    def list_usernames(self):
        '''
            Get all usernames
        '''
        return [
            user.username for user in self.users
        ]

    def remove_user(self, username: str):
        '''
            Remove user by username
        '''
        self.load_users()
        if username in self.list_usernames():
            self.users = self.find_user(username).remove_user()
        self.save_users()

    def clear_users(self):
        '''
            Remove all users
        '''
        for user in self.users:
            user.remove_user()

    def save_users(self):
        '''
            Save user data
        '''
        users_data = {
            'users': {
                user.username: user.to_dict(self.SAVE_USERS_KEEP_DETAIL) for user in self.users
            }
        }
        with open(PSNUSERS_USERS_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=4)
        
        return (True, 'OK')