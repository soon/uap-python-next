all: test

test: clean
	@mkdir -p tmp
	@PYTHONPATH=tmp python setup.py develop -d tmp
	@# run all tests
	@PYTHONPATH=tmp python ua_parser_next/user_agent_parser_test.py
	@# run a single test
	@#PYTHONPATH=tmp python ua_parser_next/user_agent_parser_test.py ParseTest.testStringsDeviceBrandModel

clean:
	@find . -name '*.pyc' -delete
	@rm -rf tmp \
	   ua_parser_next.egg-info \
	   dist \
	   build \
	   ua_parser_next/_regexes.py

release: clean
	python setup.py sdist bdist_wheel
	twine upload -s dist/*

.PHONY: all test clean release
