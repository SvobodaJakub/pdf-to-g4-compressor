JBIG2ENC="jbig2"

for f in *.pdf; do
  origpdf="$f.orig.pdf"
  mv "$f" "$origpdf"

  echo "Processing $f..."

  # Create temporary directory for intermediate files (jbig2enc doesn't like spaces in filenames)
  TMPDIR="tmp_jbig2_$$"
  mkdir -p "$TMPDIR"

  # Determine number of pages in PDF
  # Use pdfinfo if available, otherwise try identify
  if command -v pdfinfo >/dev/null 2>&1; then
    num_pages=$(pdfinfo "$origpdf" 2>/dev/null | grep "^Pages:" | awk '{print $2}')
  else
    # Fallback: use identify (slower but works)
    num_pages=$(gm identify "$origpdf" 2>/dev/null | wc -l)
  fi

  if [ -z "$num_pages" ] || [ "$num_pages" -eq 0 ]; then
    echo "Error: Could not determine number of pages in $origpdf"
    rm -rf "$TMPDIR"
    continue
  fi

  echo "PDF has $num_pages pages"

  # Convert PDF to individual PBM files (one per page) for jbig2enc
  # GM doesn't handle %04d pattern, so we loop through pages manually
  # GM page indexing starts at 0: page[0] is first page

  echo "Converting pages to PBM (non-dither)..."
  for i in $(seq 0 $((num_pages - 1))); do
    page_num=$(printf "%04d" $i)
    echo "  Page $((i+1))/$num_pages..."
    gm convert -density 310 "$origpdf[$i]" \
      -background white -flatten \
      -despeckle -colorspace gray +dither -colors 2 \
      -normalize -level 10%,90% -type Bilevel \
      "$TMPDIR/page-$page_num.pbm"
  done

  echo "Converting pages to PBM (dither)..."
  for i in $(seq 0 $((num_pages - 1))); do
    page_num=$(printf "%04d" $i)
    echo "  Page $((i+1))/$num_pages..."
    gm convert -density 310 "$origpdf[$i]" \
      -background white -flatten \
      -despeckle -colorspace gray -colors 2 \
      -normalize -level 10%,90% -type Bilevel \
      "$TMPDIR/dither-page-$page_num.pbm"
  done

  # Debug: List created PBM files
  echo "PBM files created:"
  ls -lh "$TMPDIR"/page-*.pbm 2>/dev/null || echo "No non-dither PBM files found!"
  ls -lh "$TMPDIR"/dither-page-*.pbm 2>/dev/null || echo "No dither PBM files found!"

  # Normalize all PBM files to A4 portrait dimensions (2562x3625 at 310 DPI)
  # This ensures consistent page sizes for jbig2enc (prevents invalid output for non-standard sizes)
  echo "Normalizing PBM files to A4 portrait dimensions..."
  A4_WIDTH=2562
  A4_HEIGHT=3625

  for pbm in "$TMPDIR"/page-*.pbm "$TMPDIR"/dither-page-*.pbm; do
    [ -f "$pbm" ] || continue
    # GraphicsMagick: resize to fit within A4, then extend to exact A4 dimensions with white background
    # -resize fits image within dimensions without stretching
    # -gravity center positions image in center
    # -extent sets canvas to exact A4 size, filling with background color
    gm convert "$pbm" -resize ${A4_WIDTH}x${A4_HEIGHT} -background white -gravity center -extent ${A4_WIDTH}x${A4_HEIGHT} "$pbm.tmp.pbm"
    mv "$pbm.tmp.pbm" "$pbm"
  done

  echo "Normalized PBM files:"
  ls -lh "$TMPDIR"/page-*.pbm 2>/dev/null | head -3

  # Convert PBM files to JBIG2 with symbol dictionary (better compression for multi-page)
  # -s: use symbol mode (text region coder with dictionary)
  # -p: produce PDF ready data
  # -b: output file root name (basename)
  # -a: automatic thresholding
  # -d: duplicate line removal (TPGD)
  # -t: symbol matching threshold (default 0.92, lower = more aggressive)
  # Use simple filenames without spaces for jbig2enc
  cd "$TMPDIR"

  echo "Running jbig2enc for non-dither version..."
  "$JBIG2ENC" -s -p -a -d -t 0.97 -b output page-*.pbm

  echo "Running jbig2enc for dither version..."
  "$JBIG2ENC" -s -p -a -d -t 0.97 -b dither-output dither-page-*.pbm

  cd ..

  # Debug: List created JBIG2 files
  echo "JBIG2 files created:"
  ls -lh "$TMPDIR"/output.* 2>/dev/null || echo "No non-dither JBIG2 files found!"
  ls -lh "$TMPDIR"/dither-output.* 2>/dev/null || echo "No dither JBIG2 files found!"

  # Convert JBIG2 files to PDF/A using custom script
  echo "Creating PDF from JBIG2..."
  python3 ./"jbig2pdf.py" "$TMPDIR/output" "$f"
  python3 ./"jbig2pdf.py" "$TMPDIR/dither-output" "$f.dither.pdf"

  rm -rf "$TMPDIR"

done
