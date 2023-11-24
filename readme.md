# HTML Parser

## Parameters

| Category | Name            | Type             | Usage                                                        |
| -------- | --------------- | ---------------- | ------------------------------------------------------------ |
| ID       | id_attr         | str              | The column name used to store the node id.                   |
| Label    | label_attr      | str              | The column name used to store the label (if it exists).      |
| Label    | label_generator | str              | The method used to generate a new label.<br/> *You can choose to generate in sequence or randomly* |
| Position | use_position    | bool             | Set to false to use full page, otherwise, use window_size.   |
| Position | window_size     | tuple            | The window size, denoted as (x, y, width, height).           |
| Position | rect_dict       | dict[str, tuple] | The sizes of elements, stored as {bid: (x, y, width, height)}<br/> *Recommended to use with specific id* |
| Tag      | parent_chain    | bool             | Set to true if you want to preserve all parent tags for labeled elements. |
| Tag      | keep_elem       | list[str]        | All the elements that need to be preserved.                  |
| Tag      | obs_elem        | list[str]        | All elements that should be preserved if they satisfy specific rules. |
| Prompt   | prompt          | str              | The method used to generate parsed HTML.<br/> *Choices: xml, refine* |

## Usage

Examples can be found in `html_parser.py`.
