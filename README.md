# mimic

## Installing pyvirtualcam

[pyvirtualcam](https://github.com/letmaik/pyvirtualcam/) requires that some DLLs  
are pre-installed on the system. To install them, run the following script in  
the project root directory as an administrator.

```shell
pipenv run install_dlls
```

DLLs can be uninstalled by running the following command in the project root  
directory as an administrator.

```shell
pipenv run uninstall_dlls
```

## Running aiohttp with aiortc Support

Access to the webcam requires that the webpage is secured using SSL/HTTPS. Self-signed SSL keys must be created for development. This can be done with a pip-env script:

```shell
pipenv run ssl_gencerts
```

Keys and certificates will be written to the `certs/` directory. The server can be started with the SSL keys as follows:

```shell
cd demos
python webcam.py --cert-file ../certs/selfsigned.cert --key-file ../certs/selfsigned.pem
```
