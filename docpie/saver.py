class Saver(object):

    def __init__(self):
        self.points = []

    def save(self, element, token):
        self.points.append(
            (element, element.set_save_point(), token.dump_value()))

    def rollback(self, element, token):
        '''Cancel one modify by element'''
        points = self.points
        while points:
            ele, ele_value, tk_value = points.pop()
            ele.load_save_point(ele_value)
            if ele is element:
                token.load_value(tk_value)
                return True
        else:
            raise RuntimeError('fixme: rollback failed for %s/%s',
                               element, token)
    #
    # def del_save(self, element):
    #     points = self.points
    #     while points.pop() is not element:
    #         pass
    #     else:
    #         raise RuntimeError('fixme: del_save failed for %s', element)
