from html_tools import HtmlParser
from html_tools import mind2web_keep_attrs, basic_attrs
from html_tools import print_html_object

# For vimium
def vimium_sample():
    with open('sample/sample2.html', 'r') as f:
        src = f.read()
    
    args = {
        'use_position': False,
        'label_generator': 'order',
        'id_attr': 'backend_node_id',
        'label_attr': 'new_label',
        'attr_list': mind2web_keep_attrs,
        'keep_elem': ['152601', '152608', '151562', '152385', '153864', '152954', '153204', '154499', '155142', '155316'],
        'prompt': 'refine',
    }
    
    hp = HtmlParser(src, args)
    hp.prune_tree(2)
    res = hp.parse_tree()
    
    return hp, res

# For mind2web
def mind2web_sample():
    with open('sample/sample3.html', 'r') as f:
        src = f.read()
    
    args = {
        'use_position': False,
        'id_attr': 'backend_node_id',
        'label_attr': 'temp_clickable_label',
        'label_generator': 'order',
        'attr_list': mind2web_keep_attrs,
        'keep_elem': ['13257', '13272'],
    }
    
    hp = HtmlParser(src, args)
    hp.prune_tree(2)
    res = hp.parse_tree()
    
    return hp, res

def basic_sample():
    with open('sample/sample4.html', 'r') as f:
        src = f.read()

    args = {
        'use_position': True,
        'window_size': (0, 100, 200, 100),
        'rect_dict': {
            '0': (0, 0, 100, 100),
            '3': (101, 50, 100, 100),
        },
        'label_attr': 'temp_clickable_label',
        'label_generator': 'order',
        'attr_list': basic_attrs,
        'keep_elem': ['2'],
        'parent_chain': True,
        'prompt': 'refine',
    }

    hp = HtmlParser(src, args)
    res = hp.parse_tree()
    
    bid = hp.id_label_converter('A')
    print(bid, hp.get_segment(bid))
    
    return hp, res

# For our data
def own_sample():
    with open('sample/sample5.html', 'r') as f:
        src = f.read()
    
    args = {
        'use_position': False,
        'regenerate_label': True,
        'label_generator': 'order',
        # 'id_attr': 'temp_id',
        'label_attr': 'id',
        'attr_list': [],
        'prompt': 'new_data',
    }
    
    hp = HtmlParser(src, args)
    res = hp.parse_tree()
    
    # you can get segment by id
    bid = hp.id_label_converter('C')
    print(bid)
    print(hp.get_segment(bid))
    
    return hp, res

if __name__ == '__main__':
    # TODO: change here to test different samples
    hp, res = own_sample()   
     
    _, cfgs = hp.get_config()
    print(cfgs)
    
    html = res.get('html', '')
    it, pt = res.get('init_time', 0), res.get('parse_time', 0)
    print(f'[Time] {it:.3f} {pt:.3f}')

    print(print_html_object(html))
    
    print(len(html))
    # with open('output/out.html', 'w') as f:
    #     f.write(html)
