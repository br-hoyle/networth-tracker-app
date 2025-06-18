with categorized as (
    select
        *,
        case
            when category = 'Investments' then
                case
                    when account_type ilike '%ira%' or account_type ilike '%401%' then 'Retirement'
                    when account_type ilike '%brokerage%' then 'Brokerage'
                    else account_type
                end
            else category
        end as cat,
        strptime(full_date, '%m/%d/%Y') as dt
    from balances
),

dates as (
    select distinct dt from categorized order by dt desc limit 2
),

current as (
    select cat, sum(balance) as current_balance
    from categorized
    where dt = (select max(dt) from dates)
    group by cat
),

last as (
    select cat, sum(balance) as last_balance
    from categorized
    where dt = (select min(dt) from dates)
    group by cat
)

select
    current.cat,
    current.current_balance,
    last.last_balance,
    current.current_balance - last.last_balance as difference
from current
left join last on current.cat = last.cat
order by current.cat;
