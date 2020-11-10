

class Test:
    att = 'class att'

    def __init__(self):
        self.att = 'instance att'


test = Test()
print(test.att, Test.att)

