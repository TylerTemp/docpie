# pyenv local 2.6.6; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 2.6.9; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 2.7; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 2.7.10; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 3.2; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 3.3.0; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 3.3.6; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 3.4.0; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 3.4.3; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local 3.5.0; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local pypy-2.0 ; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local pypy-2.6.0 ; pip install -U pip; pip uninstall -y docpie; pip install -e .
# pyenv local pypy3-2.4.0 ; pip install -U pip; pip uninstall -y docpie; pip install -e .

echo "================2.6.6==================="
pyenv local 2.6.6
python docpie/test.py

pyenv local 2.6.9
echo "================2.6.9==================="
python docpie/test.py

pyenv local 2.7
echo "================2.7==================="
python docpie/test.py

pyenv local 2.7.10
echo "================2.7.10==================="
python docpie/test.py

### pyenv local 3.1.5
### echo "================3.1.5==================="
### python docpie/test.py

pyenv local 3.2
echo "================3.2==================="
python docpie/test.py

pyenv local 3.3.0
echo "================3.3.0==================="
python docpie/test.py

pyenv local 3.3.6
echo "================3.3.6==================="
python docpie/test.py

pyenv local 3.4.0
echo "================3.4.0==================="
python docpie/test.py

pyenv local 3.4.3
echo "================3.4.3==================="
python docpie/test.py

pyenv local 3.5.0
echo "================3.5.0==================="
python docpie/test.py

pyenv local 3.5.1
echo "================3.5.1==================="
python docpie/test.py

pyenv local pypy-2.0
echo "================pypy-2.0==================="
python docpie/test.py

pyenv local pypy-2.6.0
echo "================pypy-2.6.0==================="
python docpie/test.py

pyenv local pypy3-2.4.0
echo "================pypy3-2.4.0==================="
python docpie/test.py


echo "DONE"

pyenv local --unset
find . -name "*.pyc" -exec rm {} \;
find . -name ".DS_Store" -exec rm {} \;
