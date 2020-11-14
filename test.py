

class test:
    title: str = '45'
    def __init__(self):
        self.title = 'not hello'
        self._title = 'hello'


a = test()
print(dir(test))
