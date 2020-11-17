from enum import Enum


class E(Enum):
    x = 1
    b = 2


print(E.__getitem__('x'))
