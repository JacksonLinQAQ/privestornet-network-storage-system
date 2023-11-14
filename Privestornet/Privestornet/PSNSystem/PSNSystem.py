# <-- PSNSystem --> #

# Required modules
import os, sys, shutil, json, datetime, string
from typing import TypeAlias, Literal
from Privestornet.PSNUsers.PSNUsers import User, Users
from Privestornet.PSNPath.PSNPath import *

# Define data types
SYSTEMCONFIG: TypeAlias = Literal['system-name', 'system-id', 'system-version', 'system-setup']

# Concatenate path function
def concatpath(*args):
    return os.path.join(*args).replace('\\', '/').strip('/')

# System Config
class SystemConfig:
    def __init__(self):
        self.load_system_config()

    def load_system_config(self):
        '''
            Load all system configuration
        '''
        if os.path.exists(PSNSYSTEM_CONFIG_PATH):
            with open(PSNSYSTEM_CONFIG_PATH, 'r', encoding='utf-8') as f:
                self.system_config = json.load(f)
        else:
            self.system_config = {
                "system-name": "My Privestornet",
                "system-id": None,
                "system-version": "DEVB23101",
                "system-setup": False,
                "system-activation-code": None,
                "system-activation-status": False
            }

            self.save_system_config()

    def modify_system_config(self, config: SYSTEMCONFIG, value: int | str | bool):
        '''
            Modify system configuration
        '''
        self.load_system_config()
        self.system_config[config] = value
        self.save_system_config()

    def get_system_config(self, config: SYSTEMCONFIG):
        '''
            Get system configuration
        '''
        self.load_system_config()
        return self.system_config[config]

    def save_system_config(self):
        with open(PSNSYSTEM_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.system_config, f, indent=4)

# Accessed User
class AccessedUser:
    def __init__(self, ip: str, users: Users):
        self.ip = ip
        self.path: str = None
        self.user: User = None
        self.users: Users = users
        self.date = datetime.datetime.now().strftime(r'%Y-%m-%d %H:%M:%S')
        self.accessed_page: list[tuple[str, dict]] = []

    def is_login(self):
        '''
            Check if user is logged in
        '''
        return self.user is not None

    def access(self, url: str, params: dict):
        '''
            Access a page
        '''
        self.refresh(self.users)
        self.accessed_page.append((url, params))

    def login(self, username: str, password: str):
        '''
            Login to the system
        '''
        self.refresh(self.users)
        user = self.users.find_user(username)
        if user and user.password == password:
            self.user = user
            return (True, f'Login success as {username}')
        else:
            return (False, 'Incorrect username or password')

    def logout(self):
        '''
            Logout of the system
        '''
        self.refresh(self.users)
        self.user = None

    def refresh(self, users: Users):
        '''
            Refresh the user object
        '''
        self.users = users

        if self.is_login():
            self.user = self.users.find_user(self.user.username)
            for data in self.user.received_data:
                if not os.path.exists(data.sent_data.fullpath):
                    self.user.received_data.remove(data)
            self.users.save_users()

    def to_dict(self):
        '''
            Convert the accessed user object to a dictionary
        '''
        self.refresh()
        return {
            'ip': self.ip,
            'user': self.user.to_dict() if self.is_login() else None,
            'date': self.date,
            'accessed_page': self.accessed_page
        }

    def concat_location(self, location: str):
        '''
            Concat the current path with the location and return it
        '''
        return concatpath(self.path, location)

# System object
class System:
    def __init__(self):
        # PSNUsers
        if not os.path.exists(PSNUSERS_PATH):
            os.makedirs(PSNUSERS_PATH)
        if not os.path.exists(PSNUSERS_USERS_DATA_PATH):
            os.makedirs(PSNUSERS_USERS_DATA_PATH)
        if not os.path.exists(PSNUSERS_PUBLIC_DATA_PATH):
            os.makedirs(PSNUSERS_PUBLIC_DATA_PATH)
        if not os.path.exists(PSNUSERS_USERS_CONFIG_PATH):
            with open(PSNUSERS_USERS_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump({'users': {}}, f, indent=4)

        # PSNSystem
        if not os.path.exists(PSNSYSTEM_PATH):
            os.makedirs(PSNSYSTEM_PATH)

        # PSNPath
        if not os.path.exists(PSNPATH_PATH):
            os.makedirs(PSNPATH_PATH)

        # PSNPrograms
        if not os.path.exists(PSNPROGRAMS_PATH):
            os.makedirs(PSNPROGRAMS_PATH)

        # PSNApplication
        if not os.path.exists(PSNAPPLICATION_PATH):
            os.makedirs(PSNAPPLICATION_PATH)

        # PSNPlugins
        if not os.path.exists(PSNPLUGINS_PATH):
            os.makedirs(PSNPLUGINS_PATH)

        # Initialize object
        self.users = Users()
        self.accessed_users: list[AccessedUser] = []
        self.config = SystemConfig()

    def access(self, ip: str, url: str, params: dict):
        '''
            Access a page
        '''
        self.refresh()
        for user in self.accessed_users:
            if ip == user.ip:
                break
        else:
            self.accessed_users.append(AccessedUser(ip, self.users))

        for user in self.accessed_users:
            if ip == user.ip:
                user.access(url, params)

    def find_user(self, ip: str = None, username: str = None):
        '''
            Find accessed users
        '''
        self.refresh()
        for user in self.accessed_users:
            if ip and ip == user.ip:
                return user
            elif username and user.user and username == user.user.username:
                return user

    def to_dict(self):
        '''
            Convert the system object to a dictionary
        '''
        self.refresh()
        return {
            'accessed_users': {user.ip: user.to_dict() for user in self.accessed_users}
        }

    def show_map(self):
        '''
            Print out the map of the accessed user
        '''
        self.refresh()
        data = self.to_dict()
        print(json.dumps(data, indent=4))

    def refresh(self):
        '''
            Refresh the system
        '''
        self.users = Users()
        for user in self.accessed_users:
            user.refresh(self.users)

    def log(self, ip: str, msg: str):
        '''
            Log a message
        '''
        print(f'[PSNSYSTEM-LOG] -- [{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] -- [HOST:{ip}] -- {msg}')

    def error(self, ip: str, msg: str):
        '''
            Log an error
        '''
        print(f'[PSNSYSTEM-ERROR] -- [{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] -- [HOST:{ip}] -- {msg}')