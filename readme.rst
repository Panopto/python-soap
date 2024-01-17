# python-soap

A python SOAP Panopto API client that wraps the zeep library for the heavy lifting

THIS REPOSITORY IS UNSUPPORTED
-----------------------------
This repository is provided as-is for general developer guidance.

The Panopto team does not support this repository.

License
-------

Copyright 2024 Panopto, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Updating dependencies
---------------------
This package has dependencies defined in two places: setup.py and requirements-dev.txt
The **abstract** dependencies defined in setup.py are required for **module dependencies**.
The **abstract** dependencies defined in requirements-dev.txt are only needed for **test and development** dependencies.

The following command will combine both of those abstract dependency files in order to generate the **pinned**
requirements.txt file.  This is what is used by the test systems in order to guarantee a stable testing environment.

.. code:: console
    $ pip-compile --output-file requirements.txt --annotate --header requirements-dev.txt

To update all packages, periodically re-run ``pip-compile --upgrade requirements.txt``.

To update a specific package to the latest or a specific version use the
``--upgrade-package`` or ``-P`` flag:

.. code:: console

    $ pip-compile --upgrade-package requests --output-file requirements.txt --annotate --header requirements-dev.txt

Pushing a new build of the package
----------------------------------

Make sure everything builds

.. code:: console

    tox

If that succeeds, then you can push a source package to artifactory
(This assumes that you've defined our local artifactory as "local" in
~/.pypirc).

.. code:: console

    python setup.py bdist_wheel --universal upload -r local


