mkdir -p ./data/bedmap_aux ./data/bedmap_csv

wget --content-disposition --trust-server-names -nc --directory-prefix ./data/bedmap_aux "https://raw.githubusercontent.com/antarctica/PDC_GeophysicsBook/main/book/images/Bedmap3_csv_list.txt"

wget --content-disposition --trust-server-names -nc --directory-prefix ./data/bedmap_aux "https://ramadda.data.bas.ac.uk/repository/entry/show?entryid=2fd95199-365e-4da1-ae26-3b6d48b3e6ac&output=zip.tree"

wget --content-disposition --trust-server-names -nc --directory-prefix ./data/bedmap_aux "https://ramadda.data.bas.ac.uk/repository/entry/show?entryid=f64815ec-4077-4432-9f55-0ce230f46029&output=zip.tree"

for f in ./data/bedmap_aux/*.zip; do
    unzip -o "$f" -d ./data/bedmap_aux/
done

find ./data/bedmap_aux -name '*.csv' -exec cp {} ./data/bedmap_csv/ \;

wget --content-disposition --trust-server-names -nc --directory-prefix ./data/bedmap_csv -i ./data/bedmap_aux/Bedmap3_csv_list.txt