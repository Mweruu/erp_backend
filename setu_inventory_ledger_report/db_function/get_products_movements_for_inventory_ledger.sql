DROP FUNCTION if EXISTS public.si_ledger_get_products_movements_for_inventory_ledger(integer[], integer[], integer[], integer[], date, date, integer);
CREATE OR REPLACE FUNCTION public.si_ledger_get_products_movements_for_inventory_ledger(
    IN company_ids integer[],
    IN product_ids integer[],
    IN category_ids integer[],
    IN warehouse_ids integer[],
    IN start_date date,
    IN end_date date,
    IN wizard_id integer)
  RETURNS void as
$BODY$
        DECLARE
            tr_start_date date;
            tr_end_date date;
            old_start_date date:= start_date;
            old_end_date date:= end_date;
            start_date timestamp without time zone := (start_date || ' 00:00:00')::timestamp without time zone;
            end_date timestamp without time zone:= (end_date || ' 23:59:59')::timestamp without time zone;

    BEGIN

    tr_start_date := '1900-01-01';
    tr_end_date := old_start_date - interval '1 day';

    with row_datas as (
    Select
        row_number() over(partition by T1.product_id, T1.company_id, T1.warehouse_id order by T1.inventory_date::date, T1.product_id, T1.company_id, T1.warehouse_id) as row_id,
        T1.company_id, T1.company_name, T1.product_id, T1.product_name, T1.product_category_id, T1.category_name, T1.warehouse_id, T1.warehouse_name,
        T1.inventory_date::date, sum(T1.opening_stock) as opening_stock, sum(T1.sales) as sales,  sum(T1.purchase) as purchase,  sum(T1.sales_return) as sales_return, sum(T1.purchase_return) as purchase_return,
        sum(T1.adjustment_in) as adjustment_in, sum(T1.adjustment_out) as adjustment_out, sum(T1.production_in) as production_in, sum(T1.production_out) as production_out,
        sum(T1.transit_in) as transit_in, sum(T1.transit_out) as transit_out, sum(T1.internal_in) as internal_in, sum(T1.internal_out) as internal_out,
        SUM(sum(T1.opening_stock) + sum(T1.purchase) - sum(T1.sales) + sum(T1.sales_return) - sum(T1.purchase_return) + sum(T1.adjustment_in) - sum(T1.adjustment_out) + sum(T1.production_in) - sum(T1.production_out) +
        sum(T1.transit_in) - sum(T1.transit_out) + sum(T1.internal_in) - sum(T1.internal_out)) over(partition by T1.product_id, T1.company_id, T1.warehouse_id order by T1.inventory_date::date, T1.product_id, T1.company_id, T1.warehouse_id) as closing
    From  (
        Select * from (
            Select
                move.company_id,
                cmp.name as company_name,
                move.product_id as product_id,
                prod.default_code as product_name,
                tmpl.categ_id as product_category_id,
                cat.complete_name as category_name,
                case
                    when source.usage = 'internal' and dest.usage = 'customer' then whs.id
                    when source.usage = 'customer' and dest.usage = 'internal' then whd.id
                    when source.usage = 'supplier' and dest.usage = 'internal' then whd.id
                    when source.usage = 'internal' and dest.usage = 'supplier' then whs.id
                    when source.usage = 'internal' and dest.usage = 'inventory' then whs.id
                    when source.usage = 'inventory' and dest.usage = 'internal' then whd.id
                    when source.usage = 'internal' and dest.usage = 'production' then whs.id
                    when source.usage = 'production' and dest.usage = 'internal' then whd.id
                    when source.usage = 'internal' and dest.usage = 'transit' then whs.id
                    when source.usage = 'transit' and dest.usage = 'internal' then whd.id
                end as warehouse_id,
                case
                    when source.usage = 'internal' and dest.usage = 'customer' then whs.name
                    when source.usage = 'customer' and dest.usage = 'internal' then whd.name
                    when source.usage = 'supplier' and dest.usage = 'internal' then whd.name
                    when source.usage = 'internal' and dest.usage = 'supplier' then whs.name
                    when source.usage = 'internal' and dest.usage = 'inventory' then whs.name
                    when source.usage = 'inventory' and dest.usage = 'internal' then whd.name
                    when source.usage = 'internal' and dest.usage = 'production' then whs.name
                    when source.usage = 'production' and dest.usage = 'internal' then whd.name
                    when source.usage = 'internal' and dest.usage = 'transit' then whs.name
                    when source.usage = 'transit' and dest.usage = 'internal' then whd.name
                end as warehouse_name,
                move.date as inventory_date,
                0 as opening_stock,
                case when source.usage = 'internal' and dest.usage = 'customer' then move.product_uom_qty else 0 end as sales,
                case when source.usage = 'customer' and dest.usage = 'internal' then move.product_uom_qty else 0 end as sales_return,
                case when source.usage = 'supplier' and dest.usage = 'internal' then move.product_uom_qty else 0 end as purchase,
                case when source.usage = 'internal' and dest.usage = 'supplier' then move.product_uom_qty else 0 end as purchase_return,
                case when source.usage = 'internal' and dest.usage = 'inventory' then move.product_uom_qty else 0 end as adjustment_out,
                case when source.usage = 'inventory' and dest.usage = 'internal' then move.product_uom_qty else 0 end as adjustment_in,
                case when source.usage = 'internal' and dest.usage = 'production' then move.product_uom_qty else 0 end as production_out,
                case when source.usage = 'production' and dest.usage = 'internal' then move.product_uom_qty else 0 end as production_in,
                case when source.usage = 'internal' and dest.usage = 'transit' then move.product_uom_qty else 0 end as transit_out,
                case when source.usage = 'transit' and dest.usage = 'internal' then move.product_uom_qty else 0 end as transit_in,
                0 as internal_out,
                0 as internal_in

            from stock_move move
                Inner Join stock_location source on source.id = move.location_id
                Inner Join stock_location dest on dest.id = move.location_dest_id
                LEFT JOIN stock_warehouse whs ON source.parent_path::text ~~ concat('%/', whs.view_location_id, '/%')
                LEFT JOIN stock_warehouse whd ON dest.parent_path::text ~~ concat('%/', whd.view_location_id, '/%')
                Inner Join res_company cmp on cmp.id = move.company_id
                Inner Join product_product prod on prod.id = move.product_id
                Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
                Inner Join product_category cat on cat.id = tmpl.categ_id

            Where prod.active = true and tmpl.active = true and
            move.state ='done' and move.date >= start_date and move.date <= end_date
            and not (source.usage = 'internal' and dest.usage='internal')
            --company dynamic condition
            and 1 = case when array_length(company_ids,1) >= 1 then
                case when move.company_id = ANY(company_ids) then 1 else 0 end
                else 1 end
            --product dynamic condition
            and 1 = case when array_length(product_ids,1) >= 1 then
                case when move.product_id = ANY(product_ids) then 1 else 0 end
                else 1 end
            --category dynamic condition
            and 1 = case when array_length(category_ids,1) >= 1 then
                case when tmpl.categ_id = ANY(category_ids) then 1 else 0 end
                else 1 end
        )move
        --warehouse dynamic condition
        where 1 = case when array_length(warehouse_ids,1) >= 1 then
                case when move.warehouse_id = ANY(warehouse_ids) then 1
                else 0 end
            else 1 end

    Union All

    select T.company_id, T.company_name, T.product_id, T.product_name, T.product_category_id, T.category_name, T.warehouse_id, T.warehouse_name, old_start_date as inventory_date, T.opening_stock,
    0,0,0,0,0,0,0,0,0,0,0,0
    from si_ledger_get_products_opening_stock(company_ids, product_ids, category_ids, warehouse_ids, tr_start_date, tr_end_date) T

    Union All

    -- Set default 0 value for each transaction for each products for each warehouse
    Select T.company_id, T.company_name, T.product_id, T.product_name, T.product_category_id, T.category_name, T.warehouse_id, T.warehouse_name, generate_series(start_date, end_date, '1 day'::interval)::date as inventory_date
    , 0 as opening_stock, 0,0,0,0,0,0,0,0,0,0,0,0
    From (
	Select cmp.id as company_id, cmp.name as company_name, prod.id as product_id, prod.default_code as product_name, ware.id as warehouse_id, ware.name as warehouse_name, cat.id as product_category_id, cat.complete_name as category_name
	From
		product_product prod, product_template tmpl, product_category cat, stock_warehouse ware, res_company cmp
	where prod.product_tmpl_id = tmpl.id and tmpl.categ_id = cat.id and ware.company_id = cmp.id
	and prod.active = true and tmpl.active = true
	 --company dynamic condition
    and 1 = case when array_length(company_ids,1) >= 1 then
        case when cmp.id = ANY(company_ids) then 1 else 0 end
        else 1 end
    --product dynamic condition
    and 1 = case when array_length(product_ids,1) >= 1 then
        case when prod.id = ANY(product_ids) then 1 else 0 end
        else 1 end
    --category dynamic condition
    and 1 = case when array_length(category_ids,1) >= 1 then
        case when cat.id = ANY(category_ids) then 1 else 0 end
        else 1 end
    --warehouse dynamic condition
    and 1 = case when array_length(warehouse_ids,1) >= 1 then
            case when ware.id = ANY(warehouse_ids) then 1
            else 0 end
        else 1 end
    )T


    Union all

    Select
        move.company_id,
        cmp.name as company_name,
        move.product_id as product_id,
        prod.default_code as product_name,
        tmpl.categ_id as category_id,
        cat.complete_name as category_name,
        whs.id as warehouse_id,
        whs.name as warehouse_name,
        move.date,
        0 as opening,
        0 as sale,
        0 as sale_return,
        0 as purchase,
        0 as purchase_return,
        0 as adjustment_out,
        0 as adjustment_in,
        0 as production_out,
        0 as production_in,
        0 as transit_out,
        0 as transit_in,
        move.product_uom_qty as internal_out,
        0 as internal_in
    from stock_move move
        Inner Join stock_location source on source.id = move.location_id
        Inner Join stock_location dest on dest.id = move.location_dest_id
        LEFT JOIN stock_warehouse whs ON source.parent_path::text ~~ concat('%/', whs.view_location_id, '/%')
        LEFT JOIN stock_warehouse whd ON dest.parent_path::text ~~ concat('%/', whd.view_location_id, '/%')
        Inner Join res_company cmp on cmp.id = move.company_id
        Inner Join product_product prod on prod.id = move.product_id
        Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
        Inner Join product_category cat on cat.id = tmpl.categ_id
    Where prod.active = true and tmpl.active = true and move.state ='done' and move.date >= start_date and move.date <= end_date and source.usage = 'internal' and dest.usage='internal' and whs.id != whd.id
    --company dynamic condition
    and 1 = case when array_length(company_ids,1) >= 1 then
        case when move.company_id = ANY(company_ids) then 1 else 0 end
        else 1 end
    --product dynamic condition
    and 1 = case when array_length(product_ids,1) >= 1 then
        case when move.product_id = ANY(product_ids) then 1 else 0 end
        else 1 end
    --category dynamic condition
    and 1 = case when array_length(category_ids,1) >= 1 then
        case when tmpl.categ_id = ANY(category_ids) then 1 else 0 end
        else 1 end
    --warehouse dynamic condition
    and 1 = case when array_length(warehouse_ids,1) >= 1 then
            case when whs.id = ANY(warehouse_ids) then 1
            else 0 end
        else 1 end

    Union All

    Select
        move.company_id,
        cmp.name as company_name,
        move.product_id as product_id,
        prod.default_code as product_name,
        tmpl.categ_id as category_id,
        cat.complete_name as category_name,
        whd.id as warehouse_id,
        whd.name as warehouse_name,
        move.date,
        0 as opening,
        0 as sale,
        0 as sale_return,
        0 as purchase,
        0 as purchase_return,
        0 as adjustment_out,
        0 as adjustment_in,
        0 as production_out,
        0 as production_in,
        0 as transit_out,
        0 as transit_in,
        0 as internal_out,
        move.product_uom_qty as internal_in

    from stock_move move
        Inner Join stock_location source on source.id = move.location_id
        Inner Join stock_location dest on dest.id = move.location_dest_id
        LEFT JOIN stock_warehouse whs ON source.parent_path::text ~~ concat('%/', whs.view_location_id, '/%')
        LEFT JOIN stock_warehouse whd ON dest.parent_path::text ~~ concat('%/', whd.view_location_id, '/%')
        Inner Join res_company cmp on cmp.id = move.company_id
        Inner Join product_product prod on prod.id = move.product_id
        Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
        Inner Join product_category cat on cat.id = tmpl.categ_id
    Where prod.active = true and tmpl.active = true and move.state ='done' and move.date >= start_date and move.date <= end_date and source.usage = 'internal' and dest.usage='internal' and whs.id != whd.id
    --company dynamic condition
    and 1 = case when array_length(company_ids,1) >= 1 then
        case when move.company_id = ANY(company_ids) then 1 else 0 end
        else 1 end
    --product dynamic condition
    and 1 = case when array_length(product_ids,1) >= 1 then
        case when move.product_id = ANY(product_ids) then 1 else 0 end
        else 1 end
    --category dynamic condition
    and 1 = case when array_length(category_ids,1) >= 1 then
        case when tmpl.categ_id = ANY(category_ids) then 1 else 0 end
        else 1 end
    --warehouse dynamic condition
    and 1 = case when array_length(warehouse_ids,1) >= 1 then
            case when whd.id = ANY(warehouse_ids) then 1
            else 0 end
        else 1 end
    )T1
    Group by T1.company_id, T1.company_name, T1.product_id, T1.product_name, T1.product_category_id, T1.category_name, T1.warehouse_id, T1.warehouse_name, T1.inventory_date::date
    )

Insert into setu_inventory_ledger_bi_report(company_id, product_id, product_category_id, warehouse_id, inventory_date,
    opening_stock, sales, purchase, sales_return, purchase_return, adjustment_in, adjustment_out, production_in, production_out, transit_in, transit_out, internal_in, internal_out, closing, wizard_id,total_in,total_out)
select
    d.company_id, d.product_id, d.product_category_id, d.warehouse_id, d.inventory_date,
    d.opening_stock, d.sales, d.purchase, d.sales_return, d.purchase_return, d.adjustment_in, d.adjustment_out, d.production_in, d.production_out, d.transit_in, d.transit_out, d.internal_in, d.internal_out, d.closing, wizard_id,
    d.purchase + d.sales_return + d.internal_in + d.adjustment_in + d.production_in + d.transit_in as total_in,
    d.purchase_return + d.sales + d.internal_out + d.adjustment_out + d.production_out + d.transit_out as total_out
from (
select
		line_one.company_id, line_one.product_id, line_one.product_category_id, line_one.warehouse_id, line_one.inventory_date::date,
    line_one.opening_stock, line_one.sales, line_one.purchase, line_one.sales_return, line_one.purchase_return, line_one.adjustment_in, line_one.adjustment_out, line_one.production_in, line_one.production_out, line_one.transit_in, line_one.transit_out, line_one.internal_in, line_one.internal_out, line_one.closing
	from
		row_datas line_one where line_one.row_id = 1
UNION ALL
select
	 r2.company_id, r2.product_id, r2.product_category_id, r2.warehouse_id, r2.inventory_date::date,
    r1.closing as opening_stock, r2.sales, r2.purchase, r2.sales_return, r2.purchase_return, r2.adjustment_in, r2.adjustment_out, r2.production_in, r2.production_out, r2.transit_in, r2.transit_out, r2.internal_in, r2.internal_out, r2.closing
	from
		row_datas r1 join row_datas r2
		                            on r1.product_id = r2.product_id
									  and r1.company_id = r2.company_id
									  and r1.warehouse_id = r2.warehouse_id
									  and r1.product_category_id = r2.product_category_id
									  and r1.row_id = r2.row_id-1
									  --where r1.closing != 0 or r2.closing != 0
									  )d order by 1,2,4,5;

END; $BODY$
LANGUAGE plpgsql VOLATILE
COST 100;
