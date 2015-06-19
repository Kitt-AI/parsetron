.PHONY: help clean clean-pyc clean-build list test test-all coverage docs release test-release sdist

# https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "testall - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "test-release - package and upload a release to the test server of PyPI"
	@echo "test-install - pip install from the test server of PyPI"
	@echo "sdist - package"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info
	rm -rf htmlcov/

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 parsetron test

test:
	# py.test
	py.test --genscript=runtests.py
	python2.7 runtests.py
	pypy runtests.py
	rm runtests.py

test-all:
	tox

coverage:
	coverage run --source parsetron setup.py test
	coverage report -m
	# coverage html
	# open htmlcov/index.html

docs:
	# rm -f docs/parsetron.rst
	# rm -f docs/modules.rst
	# sphinx-apidoc -o docs/ parsetron
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

test-release: clean
	# pypitest is defined in your ~/.pypirc file
	python setup.py sdist upload -r pypitest
	python setup.py bdist_wheel upload -r pypitest

test-install:
	pip install -i https://testpypi.python.org/pypi parsetron

sdist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
