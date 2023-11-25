def print_html_object(obj: str='') -> str:
    tab_cnt = 0
    result, content, sep = '', '', ''
    last_is_left, last_is_right = False, False
    for ch in obj:
        if ch == '<':
            result += '\n'
            if len(content.strip()) > 0:
                result += sep + content.strip() + '\n'
            result += sep + '<'
            
            tab_cnt += 1
            sep = '  ' * tab_cnt
            
            content = ''
            last_is_right = False
            last_is_left = True
        elif ch == '>':
            if last_is_left:
                result += content
            else:
                if last_is_right:
                    result += '\n'
                if len(content.strip()) > 0:
                    result += sep + content.strip() + '\n'
            
            tab_cnt -= 1
            sep = '  ' * tab_cnt
            
            if not last_is_left:
                result += sep
            
            result += '>'
            content = ''
            
            last_is_right = True
            last_is_left = False
        else:
            content += ch
    
    return result