import re

getbalance_preffixes = ['сколько', 'баланс', 'cостояние', ]
plus_preffixes = ['+', 'плюс', 'заработ', 'добав', 'прибав', ]
minus_preffixes = ['-', 'минус', 'потрат', 'трат', 'убав', 'отнят', 'отним', ]
detail_preffixes = ['детализация', ]


def parse_msg(message):
    """returns first in line number as value and rest of the string as description"""
    match = re.search('\d+', message)
    if match:
        value, category = int(match.group(0)), message[match.end():].strip()
        category = category if category else 'Разное'
        return {'value': value, 'description': category}
    else:
        return None
