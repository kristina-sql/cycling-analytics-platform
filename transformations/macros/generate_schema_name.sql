{% macro generate_schema_name(custom_schema_name, node) %}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name }}
  {%- endif -%}
{% endmacro %}

--added this macro because due to one schema in profiles different layers 
--were all under one analytics umbrella