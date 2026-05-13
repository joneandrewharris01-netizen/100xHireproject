@echo off
REM Standalone RevOps Intel pipeline. Run from anywhere.
pushd D:\Projects\my-project
"C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe" -m agents.revops_intel.run %*
popd
