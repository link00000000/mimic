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

## Examples

### Gray

A looping grayscale animation from illumination 0 to 255

```shell
pipenv ./pyvritualcam-gray.py
```

### Rainbow

A looping HSV animation from value 0 to 255

```shell
pipenv ./pyvirtualcam-rainbow.py
```

