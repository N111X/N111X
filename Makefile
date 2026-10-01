PY ?= python3
.PHONY: build-readme install png clean
install:
	$(PY) -m pip install -r generator/requirements.txt
build-readme:
	$(PY) generator/build.py
png:
	$(PY) generator/build.py --png --apng
clean:
	rm -f generator/preview.png assets/*.png assets/avatar.apng
