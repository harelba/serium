init:
	pip install -r requirements.txt
	brew install pandoc || true
	go get github.com/campoy/embedmd
	pip install tox tox-pyenv wheel twine

test:
	tox

create-doc:
	embedmd docs/README.md > docs/.README.generated
	pandoc --from=markdown --to=rst --output=./README.rst docs/.README.generated

upload-to-testpypy:
	rm -vf ./dist/*.whl
	./setup.py bdist_wheel
	twine upload --repository pypitest dist/*
