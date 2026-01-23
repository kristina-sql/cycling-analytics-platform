{{ config(materialized='table') }}


--zones must be maintained in the same historical way as FTP tests (~each 6 weeks)
--maybe in the future can explore ways of getting this data directly from Zwift
--and bellow I am using model zones like Coggan (7 zones) but including only 4 it is my custom approach
{% set zones = [
  {'zone_number': 1, 'zone_name': 'Active Recovery',    'zone_label': 'Z1', 'low': 0.00, 'high': 0.55, 'benefit': 'Recovery, very easy spinning'},
  {'zone_number': 2, 'zone_name': 'Endurance',          'zone_label': 'Z2', 'low': 0.55, 'high': 0.75, 'benefit': 'Aerobic endurance, base fitness'},
  {'zone_number': 3, 'zone_name': 'Tempo',              'zone_label': 'Z3', 'low': 0.75, 'high': 0.90, 'benefit': 'Muscular endurance, steady hard riding'},
  {'zone_number': 4, 'zone_name': 'Lactate Threshold',  'zone_label': 'Z4', 'low': 0.90, 'high': 9.99, 'benefit': 'Increase FTP, sustainable hard efforts'},
] %}


with ftp as (
  select
    ftp_id,
    ftp_watts
  from {{ ref('dim_ftp') }}
),

zone_defs as (
  -- turn the Jinja list into rows
  {% for z in zones %}
  select
    {{ z.zone_number }}::int as zone_number,
    '{{ z.zone_name }}'::varchar(50) as zone_name,
    '{{ z.zone_label }}'::varchar(20) as zone_label,
    {{ z.low }}::decimal(5,2) as ftp_pct_low,
    {{ z.high }}::decimal(5,2) as ftp_pct_high,
    '{{ z.benefit }}'::text as training_benefit
  {% if not loop.last %} union all {% endif %} 
  {% endfor %}
),

final as (
  select
    f.ftp_id,
    zd.zone_number,
    zd.zone_name,
    zd.zone_label,
    zd.ftp_pct_low,
    zd.ftp_pct_high,
    -- don’t want to round up and accidentally overshoot, floor rounds a number down
    floor(f.ftp_watts * zd.ftp_pct_low)::int as watts_low,
    floor(f.ftp_watts * zd.ftp_pct_high)::int as watts_high,
    zd.training_benefit
  from ftp f
  cross join zone_defs zd
)

select * 
from final
