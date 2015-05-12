#!/usr/bin/env python
import os
import sys
import platform
import re
import socket
import subprocess
import tempfile


"""
main

Configures a new Chameleon project and performs the setup of its Apache
virtual host and rewrite module.

return 0 : success
return 1 : general fail
return 5 : insufficent priviledges
"""
def main():
    exit_code = 0
    config = {}
    config['platform']       = platform.system().lower()
    config['dist']           = ''
    config['proj_name']      = ask_name('project')
    config['default_view']   = ask_name('view')
    config['default_config'] = 'config.php.default'
    config['db_info']        = {'name':'', 'user':'', 'pass':'', 'host':''}

    if (admin_or_root()):

        if (config['platform'] == 'linux'):
            config['dist'] = platform.linux_distribution()[0].lower()

        set_apache_locations(config)
        setup_repo()
        db_config(config)        
        write_config_file(config)
        create_vhost(config)
        enable_mod_rewrite()
        restart_apache(config)

        print (config)
    else:
        print('Insufficent Priviledges\nPlease run as root or admin user.')
        exit_code = 5
    
    sys.exit(exit_code)


"""
admin_or_root

Checks for adminstrator or root priviledges.

return True  : Sufficent priviledges.
return False : Insufficent priviledges.
"""
def admin_or_root():
    auth = False
    if (os.geteuid() == 0):
        auth = True

    return auth


"""
ask_name

Asks the user for names for different purposes with validation for each
sort of purpose.

return string : A valid string with it's first letter capitalized per
the given purpose.
"""
def ask_name(purpose):
    ask  = True
    name = ''

    while (ask):
        name = str(raw_input('What is the Name of your '+purpose.capitalize()+'?\n--> '))

        if (valid(name, 'name')):
            ask = False
        else:
            print('Invalid Project Name')

    return name


"""
valid

Used to validate user responses (strings)
for a given purpose (purpose).

param string
param purpose

return True  :
return False :
"""
def valid(string, purpose):
    response = True
    if (purpose == 'name'):
        NAME_MAX = 255; 
        response = 1<=len(string)<= NAME_MAX and "/" not in string and "\000" not in string and '*' not in string

    if (purpose == 'ip'):
        try: 
            socket.inet_aton(string)
        except socket.error:
            response = False

    if (purpose == 'email'):
        if re.match(r"[^@]+@[^@]+\.[^@]+", string) is None:
            response = False

    if (purpose == 'path'):
        NAME_MAX = 255; 
        response = 1<=len(string)<= NAME_MAX and  "\000" not in string

    return response

"""
set_apache_locations

Finds the needed Apache configuration locations/files, and stores them
in the configuration dict.

param config {} : Necessary configuration data.
return True  : Successfully set Apache locations into config.
return False : Failed to set Apache locations into config.
"""
def set_apache_locations(config):
    if (config['platform'] == 'linux'):
        if (config['dist'] == 'ubuntu' or config['dist'] == 'debian'):
            config['apache_conf'] = os.path.abspath('/etc/apache2/apache2.conf')
            config['vhost_dir'] = os.path.abspath('/etc/apache2/sites-enabled')


"""
create_vhost

Create an Apache virtual host for the project.
"""
def create_vhost(config):
    vhost       = ''
    ip          = '*'
    admin       = 'webmaster@localhost'
    name        = ''
    locale      = ''
    vhost_file  = open(config['vhost_dir']+'/'+config['proj_name']+'.conf', 'w')

    # Strings we need to use for the UI:
    ask_about_ip      = 'Project requires specification of IP address? [y|n]\n--> '
    ask_for_ip        = 'What IP would you like to use?\n--> '
    ask_about_admin   = 'Would you like to specify a ServerAdmin? [y|n]\n--> '
    ask_for_admin     = 'What email would you like to set as ServerAdmin?\n--> '
    ask_for_name      = 'What is the ServerName?\n--> '
    ask_for_locale    = 'In which directory is the project located?\n--> '
    ip_validation_err = '! IP address given is not valid !'
    name_error        = '! Name given is not valid !'
    filesystem_error  = '! Not a Valid !'

    # Ask the things:
    if (raw_input(ask_about_ip)[0].lower() == 'y'):
        ip = raw_input(ask_for_ip)
        while not valid(ip, 'ip'):
            print ip_validation_error
            ip = raw_input(ask_for_ip)

    if (raw_input(ask_about_admin)[0].lower() == 'y'):
        admin = raw_input(ask_for_admin)
        while not valid(admin, 'name'):
            print name_error
            admin = raw_input(ask_for_admin)
    
    name = raw_input(ask_for_name)
    while not valid(name, 'name'):
        print name_error
        name = raw_input(ask_for_name)

    locale = raw_input(ask_for_locale)
    while not valid(locale, 'path'):
        print filesystem_error
        name = raw_input(ask_for_name)

    # Write the virtual host to memory:
    vhost  = '<VirtualHost '+ip+':80>\n'
    vhost += '\tServerAdmin '+admin+'\n'
    vhost += '\tServerName '+name+'\n'
    vhost += '\tDocumentRoot '+locale+'\n'
    vhost += '\n\t<Directory '+locale+'/>\n'
    vhost += '\tOptions Indexes FollowSymLinks\n'
    vhost += '\tAllowOverride All\n'
    vhost += '\tRequire all granted\n'
    vhost += '\t</Directory>\n'
    vhost += '</VirtualHost>\n'

    # Dump vhost to the vhost file:
    vhost_file.write(vhost)
    vhost_file.close()


"""
enable_mod_rewrite

return True  : mod_rewrite is enabled.
return False : mod_rewrite not enabled.
"""
def enable_mod_rewrite():
    response = 0

    try:
        # If this command fails, exception thrown
        subprocess.check_output(['apachectl', '-M'])
        if (config['platform'] == 'linux'):

            if (config['dist'] == 'ubuntu'):
                response = subprocess.call(['a2enmod', 'rewrite'])
    except:
        response = 1

    if response == 0:
        return True
    else:
        return False


"""
restart_apache

Issues the approprate command to restart Apache.
"""
def restart_apache(config):
    if (config['platform'] == 'linux'):

        if (config['dist'] == 'ubuntu'):
            subprocess.call(['apachectl', 'restart'])

    return


"""
setup_repo

Creates a branch called chameleon that is meant to follow the
development of Chameleon so that this project can be easily updated
to the latest version if desired. Removes remote 'origin', and asks
user to specify a new remote.

TODO: the default is Y, but the if statement is counting on having an
indexed string (so a user can not leave the selection blank).
"""
def setup_repo():
    tmpfile = tempfile.TemporaryFile(mode='w')
    ask_about_repo  = 'Would you like to setup the git repo? [Y|n]\n'
    ask_about_repo += '(This should only be done directly after cloning Chameleon)\n--> '

    if (subprocess.call(['git', 'status'], stdout=tmpfile, stderr=tmpfile) == 0 and
            raw_input(ask_about_repo)[0].lower() != 'n'):
        subprocess.call(['git', 'branch', '-b', 'chameleon'], stderr=tmpfile);
        subprocess.call(['git', 'remote', 'remove', 'origin'], stderr=tmpfile);

    tmpfile.close()
    return


"""
ask_db_config

Ask user for MySQL database Setup.

return dict : Containing necessary database configuration values.
return dict : Empty, no database is to be configured.
"""
def db_config(config):
    # Ask user if they want to specify database connection information.
    # If yes ask for db {name, user, password, host} and store them
    # in config['db_info'] dict.
    # If no, nevermind.

    db_info = {}

    # Strings for communication with user.
    ask_about_mysql = 'Would you like to enter MySQL database configuration?'
    ask_about_mysql += ' [y|n]\n--> '
    ask_for_db_name = 'Database name------> '
    ask_for_db_user = 'Database username--> '
    ask_for_db_pass = 'Database password--> '
    ask_for_db_host = 'Database hostname--> '
    # Error Messages
    db_name_err = '! The name you entered is in valid !'
    db_user_err = '! The username you entered is in valid !'
    db_pass_err = '! The password you entered is in valid !'
    db_host_err = '! The hostname you entered is in valid !'


    if (raw_input(ask_about_mysql)[0].lower() == 'y'):
        db_info['name'] = raw_input(ask_for_db_name)
        while not valid(db_info['name'], 'name'):
            print(db_name_err)
            db_info['name'] = raw_input(ask_for_db_name)

        db_info['user'] = raw_input(ask_for_db_user)
        while not valid(db_info['user'], 'name'):
            print(db_user_err)
            db_info['user'] = raw_input(ask_for_db_user)

        db_info['pass'] = raw_input(ask_for_db_pass)
        while not valid(db_info['pass'], 'name'):
            print(db_pass_err)
            db_info['pass'] = raw_input(ask_for_db_pass)

        db_info['host'] = raw_input(ask_for_db_host)
        while not valid(db_info['host'], 'name'):
            print(db_host_err)
            db_info['host'] = raw_input(ask_for_db_host)

        config['db_info'] = db_info.copy()
    
    return


"""
create_config

Create a new configuration file from Chameleon's default configuration.
"""
def write_config_file(config):
    response    = True
    tmp_file    = file
    tmp_config  = ''
    config_file = file

    # Open default config and read it into a string.
    try:
        tmp_file = open(config['default_config'], 'r')
        tmp_config = tmp_file.read()
        tmp_config = tmp_config.replace('|proj_name|', config['proj_name'])
        tmp_config = tmp_config.replace('|db_name|', config['db_info']['name'])
        tmp_config = tmp_config.replace('|db_user|', config['db_info']['user'])
        tmp_config = tmp_config.replace('|db_pass|', config['db_info']['pass'])
        tmp_config = tmp_config.replace('|db_host|', config['db_info']['host'])
        tmp_file.close()

        config = open('config.php', 'w')
        config.write(tmp_config)
        config.close()
    except:
        response = False

    return response


if __name__ == '__main__':
    main()

