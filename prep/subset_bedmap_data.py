from pathlib import Path
# pyrefly: ignore [missing-import]
import pyarrow as pa
# pyrefly: ignore [missing-import]
import pyarrow.parquet as pq
# pyrefly: ignore [missing-import]
import pyarrow.compute as pc

data = Path("./data/")
bedmap3_path = data / "bedmap3.parquet"

table = pq.read_table(bedmap3_path)

date_col = table.column("date")
d1 = pc.strptime(date_col, format="%Y-%m-%d", unit="s", error_is_null=True)
d2 = pc.strptime(date_col, format="%Y-%m",    unit="s", error_is_null=True)
d3 = pc.strptime(date_col, format="%Y",       unit="s", error_is_null=True)
parsed = pc.coalesce(d1, d2, d3)

n_invalid = pc.sum(pc.is_null(parsed)).as_py()
print(f"{n_invalid} invalid/missing dates")

table = table.set_column(table.schema.get_field_index("date"), "date", parsed)

invalid_mask = pc.is_null(table.column("date"))
no_date = table.filter(invalid_mask)
no_date_path = data / "bedmap3_no_date.parquet"
print(f"{no_date.num_rows} rows with invalid dates -> {no_date_path.name}")
if no_date.num_rows != 0:
    pq.write_table(no_date, no_date_path)
else:
    print("No invalid-date rows -> no saving")

mask = pc.is_valid(table.column("date"))
table = table.filter(mask)

pq.write_table(table, data / "bedmap3_cleaned.parquet")

direct_time_subsets = [(1995,2001),(2007,2009),(2014,2017), (2020,2022)]

year = pc.year(table.column("date"))

for start, end in direct_time_subsets:
    mask = pc.and_(
        pc.greater_equal(year, start),
        pc.less_equal(year, end),
    )
    subset = table.filter(mask)
    out_path = data / f"bedmap3_{start}_{end}.parquet"
    print(f"{start}-{end}: {subset.num_rows} rows -> {out_path.name}")
    if subset.num_rows != 0:
        pq.write_table(subset, out_path)
    else:
        print(f"{subset.num_rows} rows -> no saving")
