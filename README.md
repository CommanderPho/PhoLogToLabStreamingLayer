a complete but minimal python app that allows the user to take timestampped notes to labstreaminglayer 


# Running
```bash
source .venv/bin/activate
python main.py 
python logger_app.py

```

## Installing `liblsl` binaries
https://labstreaminglayer.readthedocs.io/dev/lib_dev.html
```bash
git clone https://github.com/CommanderPho/PhoLogToLabStreamingLayer.git
cd PhoLogToLabStreamingLayer/
uv sync
source .venv/bin/activate


mkdir lib
cd lib
git clone --depth=1 https://github.com/sccn/liblsl.git
cd liblsl/
mkdir build
cd build/
cmake ..
make
sudo make install

```
