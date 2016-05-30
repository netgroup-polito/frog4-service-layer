# Service Layer execution

#### Run the service layer
You can launch the service layer by executing the following script in the root folder, optionally specifying your own configuration file (example: conf/config.ini):

        ./start_service_layer.sh [-d conf_file]

#### Useful scripts
The folder [scripts](scripts) contains some scripts that can be used to quickly perform common actions (useful in debugging/testing).

- Emulate the bringing up of a domain:

        python3 -m scripts.dd_domain_client name info_file
        
    name:       name used in double decker (use an IP address for uniqueness)
    info_file:  file containing the json with the domain informations

- Put graph for user device:
    
        python3 -m scripts.put_graph username mac port
    
    username:   Username of the graph owner
    mac:        Mac of the user device
    port:       The port of the authentication graph through which the user is reached

- Delete graph for user device:

        python3 -m scripts.del_device username mac
        
    username:   Username of the graph owner
    mac:        Mac of the user device to delete

    Note that if there is only one device, the graph will be deleted.

- Clean user sessions from database:

        mysql -u service_layer -p service_layer < scripts/db_session_clean.sql
        
- Clean domain informations from database:

        mysql -u service_layer -p service_layer < scripts/db_domain_clean.sql

- Delete both sessions and domain informations from database:

        mysql -u service_layer -p service_layer < scripts/db_clean.sql