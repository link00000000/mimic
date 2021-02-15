# mimic

## Installing pyvirtualcam

[pyvirtualcam](https://github.com/letmaik/pyvirtualcam/) requires that some DLLs are pre-installed on the system. To install
them, run the following script in the project root directory as an
administrator.

```shell
pipenv run install_dlls
```

DLLs can be uninstalled by running the following command in the project root
directory as an administrator.

```shell
pipenv run uninstall_dlls
```
