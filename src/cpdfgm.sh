
for f in *.pdf; do
  origpdf="$f.orig.pdf"
  mv "$f" "$origpdf"
  
  echo "Processing $f..."
  
  # Use GM to convert PDF directly to bilevel CCITT TIFF (GM does the bitonal conversion)
  # This creates a multi-page TIFF
  gm convert -background white -units pixelsperinch -density 310 "$origpdf" -page "a4^" -despeckle -colorspace gray +dither -colors 2 -normalize -level 10%,90% -type Bilevel -compress Group4 "$f.tmp.tif"

  echo "Processing dithered $f..."
  
  gm convert -background white -units pixelsperinch -density 310 "$origpdf" -page "a4^" -despeckle -colorspace gray -colors 2 -normalize -level 10%,90% -type Bilevel -compress Group4 "$f.tmp.dither.tif"
  
  echo "Packing TIFF in PDF $f..."

  # Convert CCITT TIFFs to PDF using img2pdf-based script
  python3 ./"tiff2pdf_img2pdf.py" "$f.tmp.tif" "$f.uncompressed.pdf"
  python3 ./"tiff2pdf_img2pdf.py" "$f.tmp.dither.tif" "$f.dither.uncompressed.pdf"
  
  python3 ./"pdf_compress.py" "$f.uncompressed.pdf" "$f"
  python3 ./"pdf_compress.py" "$f.dither.uncompressed.pdf" "$f.dither.pdf" 
done
