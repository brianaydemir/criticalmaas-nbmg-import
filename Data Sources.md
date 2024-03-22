Data Sources
============


United States - Wisconsin:
--------------------------

[On the web.](https://wgnhs.wisc.edu/catalog/publication?res_extras_element_type=Map&tags=Bedrock+Geology)

Strategy:

- Query for the list of all packages:

      https://wgnhs.wisc.edu/catalog/api/3/action/package_list

- Query for the information for a specific package:

      https://wgnhs.wisc.edu/catalog/api/3/action/package_show?id={package_id}

- Search the output for `resources` with:

  - `tag_string = Bedrock Geology`
  - `element_type = GIS Data`
