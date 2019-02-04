# Full Stack Web Development

## Project: Linux server Configuration

Setup and configure a baseline 
- Linux Server
- Secure the server
- Install Apache Webserver
- Configure Apache to host python web application using wsgi
- Install and configure Postgres Database server

**Pre-requisites:**

1. Linux Server instance on Amazon Lightsail
2. ssh access to Amazon Lightsail instance is enabled.
3. Login to Amazon Lightsail instance using
    - 'Connect using SSH' from Amazon Lightsail instance page
    - Setup ssh keypair to access from command prompt
    - Example.
```
ssh -i <AMAZON_LIGHTSAIL_PRIVATE_KEY> ubuntu@<ip address>
```

# Section 1

## Update all currently installed packages.
```language
sudo apt update

sudo apt upgrade
```

## Secure Server via Uncomplicated Firewall(UFW):

### Install UFW and show status
```
sudo apt install ufw

sudo ufw status
``` 

### Add/Delete UFW settings
- Disable all incoming traffic

```
sudo ufw default deny incoming
``` 

- Allow all outgoing requests

```
sudo ufw default allow outgoing
``` 

### SSH port access

#### Change the SSH port from 22 to 2200. 
- Enable ssh access
```
sudo ufw allow ssh
``` 
- Allow ssh traffic on port 2200
```
sudo ufw allow 2200/tcp
``` 
- Disable ssh traffic on port 22
```
sudo ufw deny 22/tcp
``` 
#### Add port 2200 on Amazon Lightsail
- Navigate to *Networking* tab on the Amazon Lightsail instance and add
   - Select 'Custom' from Application dropdown and add 2200 in port range

#### Update sshd_config file
```
vi /etc/ssh/sshd_config
```
Locate line and uncommet (remove #). Update 22 to 2200
```
# Port 22
Port 2200
```
NOTE: 
1. Disable of port 22 will not allow Amazon Lightsail 'Connect using SSH' web app.
2. Test ssh port 2220 access by connecting before disabling.
3. You can leave both the ports untill all server/application is setup and configured.

[https://www.godaddy.com/help/changing-the-ssh-port-for-your-linux-server-7306]

### HTTP (port 80)
- Allow web access via http
```
sudo ufw allow http
``` 
- Allow web access onport 80
```
sudo ufw allow 80/tcp
``` 

### NTP (port 123):Install and Configuration:

[https://linuxconfig.org/ntp-server-configuration-on-ubuntu-18-04-bionic-beaver-linux]

- Edit ntp.conf file
```
sudo nano /etc/ntp.conf
``` 
- Update section
```
# Specify one or more NTP servers

pool 0.asia.pool.ntp.org iburst 
pool 1.asia.pool.ntp.org iburst
pool 2.asia.pool.ntp.org iburst
pool 3.asia.pool.ntp.org iburst
```


### Enable UFW settings and check status

``` 
sudo ufw enable
sudo ufw status
``` 
# Section 2

## Setup new user account on Linux

### Add new_user and include into sudo group
```
sudo adduser <new_user>

sudo usermod -aG sudo <new_user>
```
### Password expiration of <new_user> . Enable <new_user> to create a new password at login.
```
sudo passwd -e <new_user>
```

### Grant sudo privileges to <new_user>. 
- Create <new_user> in sudoers.d and edit with nano
```
sudo touch /etc/sudoers.d/<new_user>

sudo nano /etc/sudoers.d/<new_user>

```
### Edit new_user in sudoers.d by adding the lines below. 
```
# User rules for grader
<new_user> ALL=(ALL) NOPASSWD:ALL
```
- NOTE: The <new_user> will be able to execute all sudo commands without password. If you don't want it then replace 'NOPASSWD' with 'ALL' in the above setting

## Setup ssh keypair for <new_user>
### SSH keygen on local machine command prompt similar to below. 
```
ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/Users/*****/.ssh/id_rsa): /Users/*****/.ssh/lightsail_new_user
```
- The above generates two files
    - lightsail_new_user (PRIVATE KEY used to connect to Amazon Lightsail instance)
    - lightsail_new_user.pub (PUBLIC KEY - copy the public key into Amazon Lightsail .ssh folder of user <new_user>. See next section below)

### Update SSH PUBLIC KEY for <new_user> on Amazon Lightsail.
- Create .ssh folder in the home directory of <new_user>
```
sudo su new_user
sudo mkdir .ssh
sudo chmod 700 .ssh

```
- Create authorized keys
```
touch .ssh/authorized_keys
chmod 600 .ssh/authorized_keys
```
- Edit authorized keys and update with content in PUBLIC KEY
    - copy the file content from 'cat /...//.ssh/lightsail_new_user.pub' into authorized_keys
```
nano .ssh/authorized_keys

```

### Configure the local timezone to UTC.
```
sudo dpkg-reconfigure tzdata
```
[https://askubuntu.com/questions/138423/how-do-i-change-my-timezone-to-utc-gmt]



# Section 3

## Setup Apache, Postgresql on Amazon Lightsail Instance
- Apache 
```
sudo apt update
sudo apt install apache2
```
- Postgresql
```
sudo apt update
sudo apt install postgresql postgresql-contrib
```
- Access Postgres 
```
sudo -i -u postgres
psql
```
- Create new role(catalog) and database(catalog) [Follow prompts to create new role/database]
```
createuser --interactive 
createdb catalog
```

- Connect to Postgres with the New User
```
sudo -i -u catalog
psql
```
- Verify connection to the catalog database as catalog role in Postgres
```
\conninfo
```
- Execute the Create Tables & Insert Into <Table> queries in the file ```pg_rawtables_itemcatalog``` and verify
```
\dt 

Select * from users;
Select * from category;
select * from items;
```

- Disable remote access to Postgres. Ensure the listen_addresses is configured to listen to only localhost and not any/all ip addresses
```
sudo -u postgres psql
show listen_addresses;
```
- Incase there are ip addresss other than 'localhost' then
```
show config_file;
```
```
sudo nano sudo nano /etc/postgresql/10/main/postgresql.conf
```

- Find the #listen_addresses line in the postgresql.conf and remove all other ips except 'localhost'
```
#------------------------------------------
# CONNECTIONS AND AUTHENTICATION
#------------------------------------------

# - Connection Settings -

#listen_addresses = 'localhost' 
```


# Section 4
## Python setup
- Check version and setup deafult to python3 incase the default version points to version 2
```
python --version
sudo rm /usr/bin/python
sudo ln -s /usr/bin/python3 /usr/bin/python
```

- Install pip3 and dependent packages
```
sudo apt install python3-pip

sudo pip3 install <package_name>
Ex. 
sudo pip3 install Flask
sudo pip3 install Flask-HTTPAuth 
sudo pip3 install Flask-SQLAlchemy 
```
NOTE: In case of permission issues or errors in package import issues in python file execution. Re-install pip3 packages using -H option.

'''
The directory '/home/ubuntu/.cache/pip/http' or its parent directory is not owned by the current user and the cache has been disabled. Please check the permissions and owner of that directory. If executing pip with sudo, you may want sudo's -H flag.
'''

```
sudo -H pip3 install Flask
```
[https://stackoverflow.com/questions/27870003/pip-install-please-check-the-permissions-and-owner-of-that-directory]

## Configure Apache to serve Python web application
## Install wsgi module for Python version 3
```
sudo apt update
sudo apt install libapache2-mod-wsgi-py3
```

## Verify/Install git
```
sudo apt update
git --version
sudo apt install git
```

- Create a new directory lightsail_catalog under /var/www for the python application
```
sudo touch /var/www/lightsail_catalog

cd /var/www/lightsail_catalog

git clone https://github.com/ravicoderev/lightsail_catalog.git
```

## Virtual Host setup

- Create ```ligtsail_catalog_app.wsgi```. This ensure the wsgi interface to excute the catalog application
```
cd /var/www/lightsail_catalog

touch lightsail_catalog_app.wsgi

```
- Setup virtual host <Directory> structure in ```lightsail_catalog.conf``` file under /etc/apache2/sites-available/

```
DocumentRoot /var/www/html/lightsail_catalog

        # lightsail_catalog app settings
        WSGIScriptAlias /catalog /var/www/lightsail_catalog/lightsail_catalog_app.wsgi
        <Directory /var/www/lisghtsail_catalog/lightsail_catalog/>
                 Order allow,deny
                 Allow from all
        </Directory>
        Alias /static /var/www/lightsail_catalog/lightsail_catalog/static
        <Directory /var/www/lightsail_catalog/lightsail_catalog/static/>
                Order allow,deny
                Allow from all
        </Directory>
        <Directory /var/www/lightsail_catalog/lightsail_catalog/templates/>
                Order allow,deny
                Allow from all
        </Directory>

```

- Add the ligtsail_catalog application virtual host files for Apache to serve and restart apache
```
sudo a2ensite lightsail_catalog

sudo service apache2 restart
```

# Section 5
## Launch application from browser
```
http://<ip address>/catalog
```
*Known Issues & Not in scope:*
1. The Login feature does not work since the feature requries Google Singin OAuth which is not configured to allow public ip addresses.
2. The above limits the application to 'View' only since all Create/Update/Delete operation requires successful sign-in.


**References**
1. https://lightsail.aws.amazon.com/ls/docs/en/articles/understanding-firewall-and-port-mappings-in-amazon-lightsail 
2. https://help.ubuntu.com/community/Sudoers
3. https://www.godaddy.com/help/changing-the-ssh-port-for-your-linux-server-7306
4. http://flask.pocoo.org/docs/1.0/deploying/mod_wsgi/
5. https://askubuntu.com/questions/138423/how-do-i-change-my-timezone-to-utc-gmt
6. https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-14-04
7. https://www.digitalocean.com/community/tutorials/how-to-set-up-apache-virtual-hosts-on-ubuntu-14-04-lts
 
