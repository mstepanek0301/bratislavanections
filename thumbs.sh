for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16
do
    magick $i.jpg -resize 480x300 ${i}_thumb.jpg
done