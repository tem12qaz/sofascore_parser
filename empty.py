class Empty:
    def __repr__(self):
        return ''

    def __str__(self):
        return ''

    def __bool__(self):
        return False

    def __int__(self):
        return -1

    def __float__(self):
        return -1.0
