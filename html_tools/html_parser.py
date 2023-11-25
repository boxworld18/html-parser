from lxml import html
import time, copy, random
import json, re, os

from .identifier import IdentifierTool
from .prompt import HtmlPrompt
from .configs import config_meta

class HtmlParser():
    def __init__(self, ctx: str, args: dict[str]={}) -> None:
        stt = time.time()
        self.dom_tree = self.ctx2tree(ctx)
        # tool related
        self.bids2label = {}
        self.bids2xpath = {}
        
        # parse args
        self.parse_args(args)
        self.init_time = time.time() - stt
        
    def parse_args(self, args: dict[str]={}) -> None:
        def attr_check(attr, type_model='str'):
            if attr is None:
                return False
            attr_type = type(attr)
            if attr_type != type(type_model):
                return False
            if attr_type == type('str') and len(attr) == 0:
                return False
            return True
        
        args = {} if args is None else args

        # [Position] use_pos: False -> use full page, otherwise use window_size
        use_position = args.get('use_position', False)
        window_size = args.get('window_size', None)
        rect = args.get('rect_dict', None)
        if use_position:
            if not attr_check(window_size, ()):
                raise ValueError('window_size must be set when use_position is True')
            if not attr_check(rect, {}):
                raise ValueError('rect_dict must be set when use_position is True')
        
        if not attr_check(rect, {}):
            rect = {}
        
        # [Label] for vimium is temp_clickable_label, otherwise keep all of it
        label_attr = args.get('label_attr', '')
        label_method = args.get('label_generator', None)
        regen_label = not attr_check(label_method)
        self.identifier = IdentifierTool(label_method)
        
        # [id] for mind2web is backend_node_id, for normal website use our method
        id_attr = args.get('id_attr', '')
        regen_id = not attr_check(id_attr)
        
        if regen_id:
            id_attr = 'temp_id'

        # [attributes] 
        keep_attrs = args.get('attr_list', [])
        if not attr_check(keep_attrs, []):
            keep_attrs = []
        
        # [Tags] for clickable elem, keep: must keep, obs: keep if follow specific rule
        parent_chain = args.get('parent_chain', False)
        keep_elem = args.get('keep_elem', [])
        obs_elem = args.get('obs_elem', [])
        
        # sanity check
        self.set_args(use_position, window_size, rect, label_attr, id_attr, keep_attrs, keep_elem, obs_elem, parent_chain)
        
        # [Prompt]
        prompt = args.get('prompt', None)
        self.prompt = HtmlPrompt(prompt)

        # traverse and get special data
        if regen_id or regen_label:
            self.mark_id()
          
    def set_args(self, use_position: bool=False, window_size: tuple=(), rect_dict: dict[str]={}, label_attr: str='', 
                 id_attr: str='', keep_attrs: list[str]=[], keep_elem: list[str]=[], obs_elem: list[str]=[], 
                 parent_chain: bool=False) -> None:
        
        self.use_position = use_position
        self.window_size = window_size
        self.rect = rect_dict
        self.label_attr = label_attr
        self.id_attr = id_attr
        self.keep_attrs = keep_attrs
        self.keep = keep_elem
        self.obs = obs_elem
        self.parent_chain = parent_chain
        
    def get_config(self):
        config = {
            'id_attr': self.id_attr,
            'keep_attrs': self.keep_attrs[:5],
            'label_attr': self.label_attr,
            'use_position': self.use_position,
            'window_size': self.window_size,
            'rect': dict(list(self.rect.items())[:3]),
            'keep_elem': self.keep[:5],
            'obs_elem': self.obs[:5],
            'parent_chain': self.parent_chain,
            'prompt_name': self.prompt.name,
            'identifier_name': self.identifier.name
        }
        
        return config, config_meta.format(**config)
        
    @staticmethod
    def ctx2tree(ctx: str) -> html.HtmlElement:
        # remove useless tags, eg. style and script
        ctx = re.sub('<!--[\W\w]*?-->', '', ctx)
        ctx = re.sub('<style[\W\w]*?>[\W\w]*?</style>', '', ctx)
        ctx = re.sub('<script[\W\w]*?>[\W\w]*?</script>', '', ctx)
        ctx = '' if ctx is None else re.sub(r'\s+', ' ', ctx).strip()
        dom_tree = html.fromstring(ctx)
        return dom_tree

    @staticmethod
    def get_root(tree: html.HtmlElement) -> html.HtmlElement:
        node = tree.xpath('//*')[0]
        while True:
            parent = node.getparent()
            if parent is None:
                break
            node = parent
        return node
    
    def id_label_converter(self, label: str) -> str:
        return self.bids2label.get(label, '')
    
    def id_xpath_converter(self, label: str) -> str:
        return self.bids2xpath.get(label, '')
        
    def mark_id(self) -> None:
        def _get_xpath_top_down(element, path='', order=0, in_svg=False, temp_id=0, i2xpath={}):
            # path
            tag = element.tag.lower()
            in_svg = in_svg or (tag == 'svg')
            
            if not in_svg and 'id' in element.attrib:
                node_id = element.attrib['id']
                path = f"//*[@id='{node_id}']"
            else:
                suffix = f'[{order}]' if order > 0 else ''
                prefix = f"*[name()='{tag}']" if in_svg else tag
                path = path + '/' + prefix + suffix
            
            # add temp id
            element.attrib['temp_id'] = str(temp_id)
            ori_label = element.attrib.get(self.label_attr, '')
            if ori_label != '':
                self.used_labels[ori_label] = True
            
            bid = str(temp_id)
            i2xpath[bid] = f'xpath/{path}'
            i2xpath[f'/{path}'] = bid
            i2xpath[f'xpath/{path}'] = bid
            i2xpath[f'xpath=/{path}'] = bid
            
            temp_id += 1
            
            # traverse node
            children = element.getchildren()
            tag_dict = {}
            id_list = []
            for child in children:
                ctag = child.tag.lower()
                if ctag not in tag_dict:
                    tag_dict[ctag] = 0
                tag_dict[ctag] += 1
                id_list.append(tag_dict[ctag])
            
            for cid, child in zip(id_list, children):
                ctag = child.tag.lower()
                cod = cid if tag_dict[ctag] > 1 else 0
                temp_id, i2x = _get_xpath_top_down(child, path, cod, in_svg, temp_id, i2xpath)
                i2xpath.update(i2x)
            
            return temp_id, i2xpath

        print('>>> Traverse Tree...')
        self.used_labels = {}
        root = self.get_root(self.dom_tree)
        _, i2xpath = _get_xpath_top_down(root)
        
        self.bids2xpath = i2xpath
    
    def parse_tree(self) -> dict[str]:
        def get_text(str: str) -> str:
            return '' if str is None else str.strip()[:500]
        
        def check_attr(attr: str, node: html.HtmlElement) -> bool:
            tag = node.tag
            if (
                ( attr == 'role' and node.attrib.get(attr, '') in ['presentation', 'none', 'link'] )
                or ( attr == 'type' and node.attrib.get(attr, '') == 'hidden' )
                or ( attr == 'value' and tag in ['option'] )
                ):
                return False
            return True
        
        def is_visible(bid: str) -> bool:
            if not self.use_position:
                return True
            
            rect = self.rect.get(bid, None)
            if rect is None:
                return False
            
            if self.window_size is None:
                return True
            
            # get window size
            wx, wy, ww, wh = self.window_size
            x, y, w, h = rect
            if x + w < wx or x > wx + ww or y + h < wy or y > wy + wh:
                return False

            return True
        
        def _dfs(node: html.HtmlElement, par_keep: bool=False) -> (str, dict[str]):
            # basic information
            bid = node.attrib.get(self.id_attr, '')
            tag = node.tag
            label = node.attrib.get(self.label_attr, '')
            
            # element which is keeped equivalent to visible
            visible = is_visible(bid)
            in_keep_list = bid in self.keep
            in_obs_list = (bid in self.obs or len(label) > 0) and visible
            keep_element = in_keep_list or in_obs_list or visible or par_keep
            
            have_label = False
            if in_keep_list or in_obs_list:
                if label is None or len(label) == 0:
                    label = self.identifier.generate()
                self.bids2label[bid] = label
                self.bids2label[label] = bid
                have_label = True
            
            # get text or alt_text of current element
            text = get_text(node.text)
            
            classes = {}
            # keep attributes if needed
            for attr in self.keep_attrs:
                if attr not in node.attrib or not check_attr(attr, node):
                    continue
                val = get_text(node.attrib[attr])
                if len(val) > 0:
                    classes[attr] = val

            have_text = len(text) > 0 or len(classes) > 0
            
            parts = []
            clickable_count = 0
            children = node.getchildren()
            for child in children:
                cres, cmsg = _dfs(child)       
                clickable_count += 1 if cmsg['have_clickable'] else 0
                if len(cres) != 0:
                    parts.append(cres)

            dom = self.prompt.subtree_constructor(parts)
            
            keep_element = keep_element and (clickable_count > 1 or have_text or have_label)
            keep_as_parent = len(dom) > 0 and self.parent_chain
            if in_keep_list or keep_element or keep_as_parent:
                dom = self.prompt.prompt_constructor(tag, label, text, dom, classes)
                
            control_msg = {
                'have_clickable': bool(clickable_count or have_text),
            }
            
            return dom, control_msg
        
        # start from here
        stt = time.time()
        root = self.get_root(self.dom_tree)
        dom, cmsg = _dfs(root)
        
        obj = {
            'html': dom,
            'parse_time': time.time() - stt
        }

        return obj

    # From mind2web, https://github.com/OSU-NLP-Group/Mind2Web/blob/main/src/data_utils/dom_utils.py
    def prune_tree(self, dfs_count: int=1, max_depth: int=3, max_children: int=30, max_sibling: int=3) -> None:
        def get_anscendants(node: html.HtmlElement, max_depth: int, current_depth: int=0) -> list[str]:
            if current_depth > max_depth:
                return []

            anscendants = []
            parent = node.getparent()
            if parent is not None:
                anscendants.append(parent)
                anscendants.extend(get_anscendants(parent, max_depth, current_depth + 1))

            return anscendants
        
        def get_descendants(node: html.HtmlElement, max_depth: int, current_depth: int=0) -> list[str]:
            if current_depth > max_depth:
                return []

            descendants = []
            for child in node:
                descendants.append(child)
                descendants.extend(get_descendants(child, max_depth, current_depth + 1))

            return descendants
        
        def get_keep_elements(tree: html.HtmlElement, keep: list[str], dfs_count: int=1, max_depth: int=max_depth,
                              max_children: int=max_children, max_sibling: int=max_sibling) -> list[str]:
            to_keep = set(copy.deepcopy(keep))
            nodes_to_keep = set()
            
            print(max_children, max_depth, max_sibling)
            
            for _ in range(max(1, dfs_count)):
                for bid in to_keep:
                    candidate_node = tree.xpath(f'//*[@{self.id_attr}="{bid}"]')
                    if len(candidate_node) == 0:
                        continue
                    
                    candidate_node = candidate_node[0]
                    nodes_to_keep.add(candidate_node.attrib[self.id_attr])
                    # get all ancestors or with max depth
                    nodes_to_keep.update([x.attrib.get(self.id_attr, '') for x in get_anscendants(candidate_node, max_depth)])
                    
                    # get descendants with max depth
                    nodes_to_keep.update([x.attrib.get(self.id_attr, '') for x in get_descendants(candidate_node, max_depth)][:max_children])
                    # get siblings within range
                    parent = candidate_node.getparent()
                    if parent is None:
                        continue
                    
                    siblings = [x for x in parent.getchildren() if x.tag != 'text']
                    if candidate_node not in siblings:
                        continue
                    
                    idx_in_sibling = siblings.index(candidate_node)
                    nodes_to_keep.update([x.attrib.get(self.id_attr, '') 
                                        for x in siblings[max(0, idx_in_sibling - max_sibling) : idx_in_sibling + max_sibling + 1]])
                
                max_children = int(max_children * 0.5)
                max_depth = int(max_depth * 0.5)
                max_sibling = int(max_sibling * 0.7)
                
                to_keep = copy.deepcopy(nodes_to_keep)

            return list(nodes_to_keep)

        # clone the tree
        new_tree = copy.deepcopy(self.dom_tree)
        nodes_to_keep = get_keep_elements(new_tree, self.keep, dfs_count)
        
        # remove nodes not in nodes_to_keep
        for node in new_tree.xpath('//*')[::-1]:
            if node.tag != 'text':
                is_keep = node.attrib.get(self.id_attr, '') in nodes_to_keep
                is_candidate = node.attrib.get(self.id_attr, '') in self.keep
            else:
                is_keep = (node.getparent().attrib.get(self.id_attr, '') in nodes_to_keep)
                is_candidate = (node.getparent().attrib.get(self.id_attr, '') in self.keep)
            
            if not is_keep and node.getparent() is not None:
                # insert all children into parent
                for child in node.getchildren():
                    node.addprevious(child)
                node.getparent().remove(node)
            else:
                if not is_candidate or node.tag == 'text':
                    node.attrib.pop(self.id_attr, None)
                if (
                    len(node.attrib) == 0
                    and not any([x.tag == 'text' for x in node.getchildren()])
                    and node.getparent() is not None
                    and node.tag != "text"
                    and len(node.getchildren()) <= 1
                ):
                    # insert all children into parent
                    for child in node.getchildren():
                        node.addprevious(child)
                    node.getparent().remove(node)
        
        self.dom_tree = new_tree