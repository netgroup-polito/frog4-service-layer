echo 'Insert the mysql password of user root.'
echo 'drop database if exists service_layer; create database service_layer; use service_layer; source db.sql;' | mysql -u root -p
echo 'Database created.'
