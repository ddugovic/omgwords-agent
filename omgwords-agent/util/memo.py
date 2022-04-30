# Currently only memoizes nullary instance methods
def memoize(f):
    var_name = f"_memo_{f.__name__}"
    def helper(self):
        if hasattr(self, var_name):
            return getattr(self, var_name)
        else:
            result = f(self)
            setattr(self, var_name, result)
            return result
    return helper


def lazy(f):
    return property(memoize(f))
