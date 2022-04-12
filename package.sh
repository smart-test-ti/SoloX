rm -rf build dist solox.egg-info
python3 -m pip install --user --upgrade setuptools wheel twine
python3 setup.py sdist bdist_wheel