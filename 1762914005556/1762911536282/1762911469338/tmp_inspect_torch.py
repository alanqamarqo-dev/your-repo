import torch, sys
print('torch', getattr(torch,'__version__',None), getattr(torch,'__file__',None))
print('has int64?', hasattr(torch,'int64'))
print('int64 attr repr:', getattr(torch,'int64',None))
print('dir starts:', dir(torch)[:80])
