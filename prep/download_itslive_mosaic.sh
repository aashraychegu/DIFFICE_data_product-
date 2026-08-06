dates=({1994..2002} {2006..2010} {2013..2018} {2020..2022})
aux_dir=./data/itslive_mosaic_aux
output_dir=./data/itslive_mosaic
max_jobs=8

process_date() {
    local date="$1"
    local aux_dir="$2"
    local output_dir="$3"

    local save_dir="$aux_dir/$date"
    local log="$save_dir/process.log"
    mkdir -p "$save_dir"
    mkdir -p "$output_dir"

    {
        echo "=== [$date] started $(date '+%Y-%m-%d %H:%M:%S') ==="

        local download_string_vx="https://its-live-data.s3.amazonaws.com/velocity_mosaic/v2.1/annual/cog/ITS_LIVE_velocity_120m_RGI19A_${date}_V02.1_vx.tif"
        local download_string_vy="https://its-live-data.s3.amazonaws.com/velocity_mosaic/v2.1/annual/cog/ITS_LIVE_velocity_120m_RGI19A_${date}_V02.1_vy.tif"

        local nc_out="$output_dir/velocity_${date}.nc"

        echo "[$date] downloading vx.tif"
        curl -f -s -C - -o "$save_dir/vx.tif" "$download_string_vx"
        echo "[$date] downloading vy.tif"
        curl -f -s -C - -o "$save_dir/vy.tif" "$download_string_vy"

    } > "$log" 2>&1
}

export -f process_date
export aux_dir
export output_dir

mkdir -p "$output_dir"

printf '%s\n' "${dates[@]}" | parallel -j "$max_jobs" \
    --joblog "$aux_dir/parallel_joblog.tsv" \
    --tagstring '{}' --line-buffer \
    process_date {} "$aux_dir" "$output_dir"

echo "All dates processed. NetCDF files in: $output_dir"