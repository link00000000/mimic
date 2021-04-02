# mimic

[![Build Release](https://github.com/link00000000/mimic/actions/workflows/build-release.yml/badge.svg?branch=master)](https://github.com/link00000000/mimic/actions/workflows/build-release.yml)

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

## Automated Builds 🔨

Builds are automatically created on commit using GitHub Actions. Build artifacts for `Windows x64` and `Windows x64 Debug` are available under GitHub actions.

### Automated Releases

If a commit is tagged with the format vX.X.X, production and debug builds will be created and a release will be made with the build artifacts attached.
