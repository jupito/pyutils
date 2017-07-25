"""Just testing."""

import string


class MyFormatter(string.Formatter):
    """..."""
    def convert_field(self, value, conversion):
        print(type(value), value)
        if conversion == 'i':
            # return iter(value)
            return list(value)
            # return (super(MyFormatter, self).convert_field(x, 's') for x in
            #         value)
        elif conversion == 'l':
            return str(value).lower()
        else:
            return super(MyFormatter, self).convert_field(value, conversion)

    def vformat(self, format_string, args, kwargs):
        words = format_string.split()
        print(words)
        # words = [super(MyFormatter, self).vformat(x, args, kwargs) for x in
        #          words]
        # words = [self.vformat(x, args, kwargs) for x in words]
        print(words)
        lst = []
        for x in words:
            if isinstance(x, str):
                print('##', type(x), x)
                # x = super(MyFormatter, self).vformat(x, args, kwargs)
                lst.append(x)
            else:
                print('##', type(x), x)
                lst.extend(x)
        return lst
        # return ' '.join(lst)

    # fmt = MyFormatter().format
    # fmt('{0!Q}', '<hello> "world"')
