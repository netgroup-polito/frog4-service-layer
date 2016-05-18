# Service Layer installation guide

Tested on ubuntu 14.04.1 and Debian stretch-testing.

#### Required packages
First of all, install required packages from your distribution repositories:

    sudo apt-get install python3-dev python3-setuptools python3-pip python3-sqlalchemy libmysqlclient-dev
    sudo pip3 install --upgrade falcon requests gunicorn jsonschema pymysql

#### DoubleDecker
The frog4-service-layer uses the [DoubleDecker](https://github.com/Acreo/DoubleDecker) messaging system to recieve informations from below domains. In order to launch the frog4-service-layer you need to install DoubleDecker.
Install the python version of the client required to run the service layer cloning the repository and following the istructions provied:

    git clone https://github.com/Acreo/DoubleDecker-py

If you need to run the message broker too, you have to install the C version of Double Decker, from the following repository:

    git clone https://github.com/Acreo/DoubleDecker
    
#### Clone this repository
Now you have to clone this repository and all the submodules. Submodules include components that are part of the service layer but that are being developed in different repositories. This lead to the necessity to clone them as well in the right folders, under the FROG4 service layer root. For this, please follow the steps below:

    git clone https://github.com/netgroup-polito/frog4-service-layer
    cd frog4-service-layer
    git submodule init && git submodule update
    
#### Create database
The FROG4 service-layer uses a local mySQL database that has to be created and initialized by executing the steps below.

- Create database and user for service layer database:
    
        mysql -u root -p
        mysql> CREATE DATABASE service_layer;
        mysql> GRANT ALL PRIVILEGES ON service_layer.* TO 'service_layer'@'localhost' IDENTIFIED BY 'SL_DBPASS';
        mysql> GRANT ALL PRIVILEGES ON service_layer.* TO 'service_layer'@'%' IDENTIFIED BY 'SL_DBPASS';    
        mysql> exit;
    
- Create tables in the service_layer db:
    
        cd frog-service-layer
        mysql -u service_layer -p service_layer < db.sql

#### Configuration
Configuration parameters are stored in [config/default-config.ini](config/default-config.ini); you can copy this file to set up your custom configuration of the service layer.
- Change the db connection:

        [db]
        connection = mysql+pymysql://service_layer:SL_DBPASS@127.0.0.1/service_layer

- Change the orchestrator endpoint:
        
        [orchestrator]
        port = ORCH_PORT
        ip = ORCH_IP
    
- Associate for each user in the DB a service graph:
    - Copy the json of the user service graph in [graphs](graphs) folder;
    - Insert/edit a row in the table user, specifying the file name of the graph in the 'service_graph' column.

#### Run the service layer
You can launch the service layer by executing the following script in the root folder, optionally specifying your own configuration file (example: conf/config.ini):

        ./start_service_layer.sh [-d conf_file]
