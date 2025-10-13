class vector:
    a=0 

    def __init__(self, a):
        self.a=a        
        print(a)    

    def __add__(self, a):
        return [x + y for x, y in zip(self.a)]

    def __sub__(self, a):       
        return [x - y for x, y in zip(a)]
    
    def __mul__(self, a):
        return [x * y for x, y in zip(a)]

class vector2D:

    def __init__(self):
        pass