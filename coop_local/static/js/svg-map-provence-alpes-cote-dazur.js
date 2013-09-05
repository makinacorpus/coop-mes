var r = Raphael('svg-map', 185, 160);
var mapSet = r.set();

mapSet.push(r.path('M 139.4 113.3 C 139.3 113.5 139.2 113.7 139 114.5 C 139.1 114.5 138.6 114.2 138.6 114.2 C 138.5 114.5 138.5 114.9 138.4 115.1 C 135.9 112.7 136.1 112.9 136.2 109.5 C 136.3 107.8 136.4 104.8 133.7 106.5 C 132.7 105.1 131.4 105.1 130.5 104.1 C 128.7 102.1 130 101.7 129.2 99.7 C 127.5 95.7 122.7 98.2 122.4 94.1 C 123.6 93.1 128.5 91.1 123.8 90.9 C 124.7 89.4 126.1 88.1 123.9 87 C 125.5 87.2 127.9 88.4 129 86.9 C 130 85.6 130.9 82.6 132.7 84.8 C 133.8 85.5 138.2 84.9 136.6 84.2 C 134.9 83.4 134.1 81.9 132.1 81.5 C 132.1 77.8 128.4 78.4 126.7 75.6 C 126.2 74.7 126.7 73 126.2 71.9 C 126.1 71.7 123.8 68.3 124.1 68.6 C 122.1 67 125.3 58.5 127.7 59.4 C 127 53.4 132.7 52.8 135.5 56.2 C 136.7 57.7 136.7 58.2 138 59.7 C 138.6 60.3 139.3 61.4 139.9 62.1 C 140.4 62.7 141.7 61.5 142.5 61.7 C 145.7 62.5 149 64.8 151 65.7 C 153.1 66.7 153.2 66.2 155.6 66.7 C 156.7 67 156.7 67.9 158.1 68.1 C 158.9 68.2 159.6 68.1 160.4 68.6 C 160.7 66.8 164.8 66 166.6 65.7 C 167 65.6 168.9 65.5 169.6 65.1 C 171 64.6 169.9 62.4 172.8 63.2 C 172 66.9 174.5 68.2 174.4 71.8 C 174.4 72.6 173.2 72.6 173 73.2 C 172.7 74 173.2 75.2 172.8 76.1 C 171.7 78 170 78.6 168.3 79.6 C 169 82.8 166.3 82.2 165.5 84.5 C 164.7 86.5 166.4 89.1 167.4 91 C 166 91.3 165.4 92.2 165.3 93.6 C 163 92.3 162.3 95.1 161 96 C 160.5 96.3 155.6 97.5 158.8 98.6 C 158.5 98.9 158.4 98.7 158.1 98.6 C 157.9 99 158.2 99.1 157.7 99.5 C 157.6 98.5 157.1 98 157 97.3 C 156.9 97.8 156.7 98.3 156.5 98.8 C 156.3 98.6 155.8 98.2 155.5 98.1 C 153.8 98.3 152.7 99.8 151.7 101.4 C 148.9 99.5 146.2 106.8 148.7 107.5 C 148.8 107.9 148.3 108.3 148.4 108.5 C 148.3 108.3 149 108.8 149 108.8 C 148.5 109.3 148.2 109.4 147.7 109.6 C 147.8 106 144.4 108.7 143.4 110.3 C 141.7 107.9 137 111.6 139.4 113.3Z').attr({'fill':'#f5f5f5','stroke':'#7d8ea5','stroke-width':'1.5','stroke-opacity':'1'}).data('href','/cartographie/?dep=06'));

mapSet.push(r.path('M 109.5 98.9 C 111.3 96.7 110.2 94.6 113 94.3 C 115 94.1 117.6 92.1 117.8 95.5 C 119.9 93 120 93.1 122.1 94 C 122.7 94.2 122.6 96.3 123.4 96.9 C 123.5 97 124.8 96.1 125.5 96.3 C 126.3 96.6 126.3 97.3 126.6 97.5 C 127.8 98.1 128.7 97.2 129.1 99.2 C 129.3 100.6 128.6 101.6 129.1 102.8 C 130.1 104.8 132.4 104.7 133.7 106.5 C 138.3 103.7 135.1 111.8 135.9 113.2 C 136.8 114.8 138.7 114.1 138 116.6 C 137.6 117.8 136.1 119.3 135 118.4 C 135.3 121.7 129.8 118.8 128.4 120.5 C 128.6 121 128.5 123.8 128.2 124.3 C 127.5 125.7 125.3 125.8 126.2 127.6 C 125.7 127.7 121.7 129.5 121.8 130.5 C 121.9 131.8 125.1 130.3 126 131 C 126.3 130.5 126.1 130.3 126.5 129.9 C 129.1 131.5 123.9 133.5 127.1 135.2 C 125.7 135.4 124.9 136.2 125.5 137.5 C 125.7 137.4 124.1 138.3 124.2 138.2 C 123.9 137.8 123 136.6 122.3 136.5 C 120 136.1 120.4 137.9 119.9 138.2 C 118.2 139 115.7 138.4 114.7 139.9 C 112.7 138.5 109.9 141.6 111.5 143.6 C 111 143.8 111.3 143.4 111.2 144 C 108.9 143.9 108 141.8 105.8 141.9 C 103.1 141.9 97.7 147.3 101.6 148 C 100.3 148.8 99.1 147.6 98.2 148.7 C 97.9 148.4 97.8 148.4 97.5 148 C 98.7 148 100.8 146.4 98.9 145 C 97.4 144 96.2 145.6 94.9 145.3 C 92.4 144.8 92.5 143.1 88.8 144.1 C 89.1 143.4 89 143.1 89.1 142.8 C 89.2 142.8 88.8 143.5 88.8 143.2 C 88.7 143 88.9 143 88.9 142.7 C 88.5 142.9 88.9 142.6 88.5 142.6 C 88.6 142.9 88.6 143.1 88.3 143.2 C 88.5 142.9 88.4 142.7 88.1 142.8 C 87.8 143 88.2 143.2 88.1 143.2 C 87.3 143.4 87.1 143.4 86.6 143.6 C 87.7 143.9 88.7 144.3 87.4 145.5 C 88 145.4 88.3 145.3 88.8 145.1 C 89 145.1 88.6 145.6 89.1 145.6 C 91.5 145.7 89.1 145.8 88 146.3 C 87.2 146.6 86 146 85.7 148.1 C 84.3 148 83.2 147.1 82.1 146.7 C 83.3 144.9 83.7 143.2 80.7 143.6 C 81.6 142 79.4 142.1 77.8 141.4 C 76.6 140.9 76.4 139.6 75.3 139.6 C 75.4 138.7 76.5 134.7 76.6 135 C 76.2 133.9 79.2 134.1 79.4 133.3 C 80 131 76.5 129.9 74.7 130 C 76.6 128.1 74.4 126.8 75.2 124.8 C 76.1 122.7 78.6 124.8 80.2 122.5 C 78.1 121.4 76.2 119.2 75.4 117.4 C 79.4 115.2 73.9 112.9 72.9 111.8 C 73.6 111.8 74.1 111.4 74.7 111.3 C 73.2 109.2 74.9 107.4 76.4 106.6 C 79.6 104.8 80.7 105.8 79.4 101.8 C 78.6 102.1 78.6 101.6 77.9 101.4 C 78.6 98.5 82.2 99 83 101.9 C 84.6 101.6 86 100.9 85.3 99 C 87 98.5 89 102.2 90.6 103.4 C 92.8 105.2 91.2 103.7 93.2 102.5 C 94.8 101.6 95.2 100 95.9 98.7 C 97.2 101.8 100 94.6 101.8 94.5 C 104 94.3 106.9 100.1 108.9 98 C 109.1 98.2 109.4 98.8 109.5 98.9Z').attr({'fill':'#f5f5f5','stroke':'#7d8ea5','stroke-width':'1.5','stroke-opacity':'1'}).data('href','/cartographie/?dep=83'));

mapSet.push(r.path('M 82.5 101 C 81.5 98.9 78.5 98.7 78.1 101.4 C 75.3 98.6 71.1 91.6 66.8 95.7 C 65.9 93.3 68.8 90.8 69.5 88.5 C 68.2 88.6 67.4 88 67.3 86.6 C 61.9 87.9 65.7 81 65.8 77.7 C 63.7 79 62.7 77.1 63.2 75.2 C 63.5 73.6 66 72.2 67.4 71.4 C 64.5 69.1 70.6 68 69.6 71.8 C 70.2 72 71.3 72 72 71.9 C 72 71.9 69.1 68.1 71.1 68.9 C 71.7 69.2 75.1 67.1 75.9 66.9 C 78.1 66.5 82.6 69 84.1 67.3 C 82.7 67.1 79.2 63.9 79.2 62.6 C 79.4 57.8 83.2 63.8 84.2 64 C 83.4 62.1 84.2 61.2 84.2 59.4 C 80.9 59.7 84.6 57.3 84.8 55.7 C 85.2 53.2 88.8 50.7 90.7 49.2 C 90.9 49.6 91 49.6 91.3 50 C 90.7 47 92.7 47.4 94.9 48.2 C 94.6 48 96.9 50.2 96.4 49.7 C 97.4 50.8 98.6 52.5 99.2 54 C 101.7 52 99 50.6 99.3 48.8 C 99.6 47.3 102.1 46.1 103.7 47.7 C 105 45.9 103.1 44.1 105.4 43.4 C 106.9 46 109.1 47.6 111.9 48.3 C 113.2 48.6 115.9 48.7 117.1 48.2 C 118.9 47.5 119.5 46.7 120.4 44.6 C 120.7 43.8 121.2 42.8 121.2 41.9 C 121.3 41.4 122.9 41.1 123.5 40.4 C 124.3 39.4 125.6 38.1 126.4 37.5 C 128.1 36.2 132 32.2 134.1 32.8 C 135.2 34.9 133.4 35.6 133.4 37.4 C 133.3 39.5 131.5 38.8 130.8 40 C 129 43.4 131.9 46.2 134.8 48.2 C 131.1 48.1 133.6 50.4 132.2 53 C 130.8 55.7 127.2 54.7 127.7 59.4 C 125.3 58.5 122.1 67 124.1 68.6 C 125.1 69.4 126.9 73.3 126.8 75.3 C 126.6 77.5 132.1 78.4 132.1 81.5 C 133.1 81.7 136.1 82.9 136.4 84.1 C 136.9 86.2 134.1 85.8 132.7 84.8 C 130.8 82.4 130.4 85.8 129.3 86.5 C 127.2 87.8 126.6 87.3 123.9 87 C 126.1 88.1 124.7 89.4 123.8 90.9 C 127.9 91.1 124.3 93.9 122.4 94.1 C 121.9 94.1 121.2 92.9 119.7 93.1 C 119.7 93.1 118.1 95.1 117.8 95.5 C 117.6 92.1 115 94.1 113 94.3 C 110.2 94.6 111.3 96.7 109.5 98.9 C 109.4 98.8 109.1 98.2 108.9 98 C 106.9 100.1 104 94.3 101.8 94.5 C 100 94.6 97.2 101.8 95.9 98.7 C 95.2 100 94.6 101 93.6 102.3 C 92.1 104.3 92.3 104.3 90.8 103.6 C 88.7 102.6 87.4 98.3 85.4 99 C 86 100.9 84.6 101.6 83 101.9 C 82.8 101.6 82.7 101.3 82.5 101Z').attr({'fill':'#f5f5f5','stroke':'#7d8ea5','stroke-width':'1.5','stroke-opacity':'1'}).data('href','/cartographie/?dep=04'));

mapSet.push(r.path('M 105.4 43.4 C 103.1 44.2 105 45.9 103.7 47.7 C 102.6 46.6 98.8 47.3 99.2 48.5 C 99.9 50.5 101.4 52.2 99.2 54 C 98.6 52.5 97.4 51.6 96.7 50.3 C 96.9 50.7 94.8 48.1 94.9 48.2 C 92.7 47.4 90.7 47 91.3 50 C 91 49.6 90.9 49.6 90.7 49.2 C 88.8 50.7 85.2 53.2 84.8 55.7 C 84.6 57.3 80.9 59.7 84.2 59.4 C 84.2 61.2 83.4 62.1 84.2 64 C 83.1 63.8 79.9 58.1 79.2 62.2 C 79 63.7 82.6 67.1 84.1 67.3 C 82.5 69 80.4 66.8 78.6 66.6 C 76.7 66.4 74 67.6 72.2 68.4 C 71.4 66.2 72.4 62.3 70.1 63.6 C 69.6 62.1 69.4 60.9 68 60.9 C 68.5 60.3 68.5 59.8 69.1 59.3 C 69 59.1 68.9 58.9 68.8 58.8 C 67.4 59.1 65.8 59.2 64.5 59.1 C 64.5 57.7 63.6 57.8 62.5 58.9 C 61.4 57.8 61.2 56.8 59.5 56.9 C 59.6 56.4 58.8 53.1 58.6 53.6 C 59.7 51.5 60.2 53.8 61.6 52.6 C 61.9 52.4 60.7 49.4 60.2 47.4 C 61.5 48 64.2 48.7 65.5 48.7 C 68.6 48.7 66.4 49.2 68.3 47.7 C 68.9 47.1 69 46.6 70.2 46.8 C 68.4 43.6 67 45.3 67.6 41.8 C 67.9 40.4 68.5 37 69.1 36.1 C 69.8 36.6 72.6 37.3 73.1 36.4 C 73.1 36.4 74 36.4 74.1 36.3 C 73.9 36 73.7 36.3 73.5 35.8 C 74.7 35.8 75.3 36 76.4 35 C 77.7 33.7 78.6 32.6 76.5 32.2 C 77.3 31.4 77.6 30.2 77.7 28.7 C 78.7 29.1 86.5 28.4 85 26.1 C 84.3 24.9 82.7 24 85.6 23.9 C 87 23.8 87.1 21.1 88.7 24 C 89.4 23.4 90.8 21.8 91.7 21.4 C 93.7 20.4 95.3 21.2 97.7 20.9 C 98.2 20.9 99.6 19.9 100.1 19.5 C 101.2 18.7 101.6 20.5 102.2 20.7 C 103.9 21.5 103.8 17.2 103.7 16.2 C 103.4 14 100.9 13.5 101.3 11.3 C 101.8 8.4 94.9 12.6 95.8 9 C 96.1 7.3 96.3 4 97 3.1 C 98.7 1.1 100.2 4.2 101.8 1.7 C 103.1 2.4 104.1 3.8 103.6 5.3 C 105.9 5.4 107.5 6.2 109.7 5.8 C 109.8 4.7 110.1 4.4 109.4 3.4 C 108.4 2.1 112.2 2.6 112.3 2.5 C 113.4 2.1 115.7 -0.8 116.7 1.9 C 117.4 4 118.2 5.7 119 7.6 C 119.6 9.1 124.3 7.5 122.6 9.9 C 123.7 11 124.3 12.7 122.9 13.9 C 122.9 13.7 123.7 14.1 123.7 14.1 C 120.7 19 136.1 19 136.4 20.2 C 136.8 21.7 136.9 22.9 137.3 24.7 C 137.8 26.6 138.9 26.9 139.4 28.2 C 141.2 32.4 138.4 29.3 135.5 30.7 C 134.2 31.4 134.5 33.7 132.6 32.7 C 132.4 32.6 129.6 35.1 129.5 35.4 C 129.3 36.1 127.1 37 126.4 37.6 C 125.5 38.2 124.8 39.3 123.7 40.5 C 122.4 41.9 120.9 41.1 120.7 43.7 C 120.7 43.6 118.9 48 119 47.8 C 117.9 48.7 111.4 49.1 110.3 47.4 C 109.7 46.6 108.4 47.1 107.6 46.4 C 106.8 45.7 105.8 44.3 105.4 43.4').attr({'fill':'#f5f5f5','stroke':'#7d8ea5','stroke-width':'1.5','stroke-opacity':'1'}).data('href','/cartographie/?dep=05'));

var group1 = r.set();
group1.push(r.path('M 32 60 C 31.6 60.6 31.6 61.4 31.9 62.6 C 33.9 61.9 35.5 62.7 36.9 63.2 C 37.2 61.5 37.6 61 38.5 59.8 C 38.7 59.5 39.5 58.3 39.6 58.1 C 39.5 58.2 41 57.1 41.3 56.8 C 39.7 56.6 37.6 56.5 38.3 54.5 C 37.4 54.5 36.8 54.3 35.8 53.5 C 35.1 54.4 33.9 55 33.3 54.9 C 32.7 57.1 31.9 58.4 30.7 59.7 C 31.2 59.7 31.5 59.9 32 60Z').attr({'fill':'#f5f5f5','stroke':'#7d8ea5','stroke-width':'1.5','stroke-opacity':'1'}));
group1.push(r.path('M 77.3 100.5 C 75 99.6 75.1 97.4 73.3 96.1 C 71.2 94.5 68.8 93.8 66.8 95.7 C 65.9 93.3 68.8 90.8 69.5 88.5 C 68.2 88.6 67.4 88 67.3 86.6 C 61.9 87.9 65.7 81 65.8 77.7 C 63.3 79.3 63.4 76.8 63.1 74.9 C 63.1 74.9 59.5 72.3 59.3 72.2 C 58.7 71.7 58.4 72.4 57.7 72.2 C 56.9 71.8 57.8 71 57.5 70.7 C 56.9 70 57.7 68.9 56.6 68.2 C 55.8 67.7 55 68.6 53.7 68.3 C 52.8 68 51.7 67.6 50.3 66.8 C 50.2 69.1 47.3 68.5 46.1 67.1 C 44.7 65.6 46.5 63.1 46.3 61.1 C 45.8 61.7 43.6 64.2 42.9 63.7 C 41.6 62.9 41 62.4 39.7 62.5 C 37.1 62.6 34.6 65.6 32 65.8 C 32.1 65.7 32.2 65.5 32.2 65.4 C 30.7 65.9 29.8 67.5 28.1 68.1 C 27.9 66 27.3 64.6 27.6 62.7 C 26.2 61.6 24.9 61.3 22.8 61.6 C 18.6 62.2 21.6 62.7 19.8 65.7 C 21.9 67.6 22.4 69.4 23.4 71.3 C 24.8 74 22.5 76.4 24.6 78.9 C 25 78.4 25.8 78.3 26.2 78 C 27.2 79.4 30.4 82.2 30.7 83.9 C 30.7 83.8 29.2 86.8 29.2 86.8 C 27.9 87.4 26.6 88.9 25.6 89.8 C 28.9 89.9 31.1 90.1 34 91.6 C 35 92.2 36.2 92.5 37.2 92.9 C 38.3 93.3 38.3 94.8 39.5 95.2 C 41.3 95.7 41 97.6 42.2 98.7 C 42.9 99.3 44.3 99.6 45.2 100.1 C 45.8 100.5 47.7 102 48.3 102 C 49.7 102.1 50.5 100.4 52 100.7 C 56.7 101.8 60 105.6 65 106.3 C 68.1 106.8 78.9 104 77.3 100.5Z').attr({'fill':'#f5f5f5','stroke':'#7d8ea5','stroke-width':'1.5','stroke-opacity':'1'}));
group1.data('href','/cartographie/?dep=84');
mapSet.push(group1);

mapSet.push(r.path('M 32.5 126.6 C 33 126.1 33.3 125.5 33.9 125.1 C 34 125.3 34 125.6 34.1 125.8 C 34.6 122.7 38.7 123.6 39.2 126 C 40 125.2 39.1 126.1 40.3 125.6 C 39.9 125.9 39.7 125.9 39.4 126.2 C 40.6 127.3 40.9 129.2 41 129.5 C 41.9 130.6 42.5 130.9 43.2 130.5 C 43.3 130.6 42.8 130.9 43.3 130.9 C 43.9 130.2 46.7 130.6 49 130.5 C 51.1 130.4 55.8 127.6 57.3 128.7 C 57 128.6 56.9 128.6 56.9 128.8 C 57.9 128.8 59 130.3 58.8 132.2 C 58.8 132.2 59.6 132.3 59.6 132.3 C 58.4 132.4 57.7 133.4 59.3 134.2 C 60.4 134.8 58.6 137.2 58.4 137.9 C 58.2 138 57.9 137.8 57.8 137.8 C 59.3 139 61 137.7 62.6 138.6 C 62.8 138.6 62.3 138.1 62.3 138.1 C 63.1 138.4 63.5 138.5 64.1 138.8 C 63.9 138.5 63.7 138.3 63.5 138 C 64.4 138.1 65.4 138.5 66.5 138.9 C 66.6 138.7 66.1 138.6 66.3 138.6 C 66.9 138.8 66.7 138.8 67 138.9 C 67.1 138.5 67.1 138.4 67.2 138.1 C 67 138.3 68.2 137.8 68.4 137.7 C 68.7 138.4 70.1 140.8 72 141.2 C 71.9 140.8 71.8 140.6 71.8 140.3 C 72.3 139.4 73.9 138.9 75.1 139.9 C 75.8 137.9 75.6 136.7 76.7 135.3 C 76.8 135.1 79.4 133.4 79.4 133.3 C 80 131 76.5 129.8 74.7 130 C 76.6 128.1 74.4 126.8 75.2 124.8 C 76.1 122.7 78.6 124.7 80.2 122.5 C 78.1 121.4 76.2 119.2 75.4 117.4 C 79.4 115.2 73.9 112.9 72.9 111.8 C 73.6 111.8 74.1 111.4 74.7 111.3 C 73.2 109.2 74.9 107.4 76.4 106.5 C 79.6 104.8 80.7 105.8 79.4 101.8 C 77.7 101.2 75.5 103.1 74.3 103.9 C 71.6 105.6 69.4 105.6 66.5 106.6 C 62.4 107.9 56.9 102 53.4 101.2 C 50.1 100.6 49.2 102.1 46 100.7 C 43.1 99.5 42.4 97.7 40.4 95.8 C 36.2 91.8 31.5 90 25.6 89.8 C 24.9 90.4 24.7 91 23.7 91.4 C 23.6 92.7 20.7 92.9 21.1 94.8 C 21.7 94.7 21.7 94.7 22.3 94.8 C 20.3 96.1 22.3 97.3 21.4 99.4 C 20.4 101.9 19.2 103.9 20.7 106.5 C 17.7 106.5 15.7 104.4 13.1 106.8 C 11.9 107.8 9.2 112.9 13.1 112 C 12.4 114 10.8 113.9 9.2 114.8 C 9.5 114.8 9.7 114.8 9.9 114.8 C 9.2 115.9 5.1 118.7 5.3 116.2 C 4.2 116.3 4.4 117.1 5.3 118.2 C 3.4 119.4 0.6 119.8 0.8 123 C 4.8 122.9 8.6 123.2 12.4 122.9 C 16.1 122.6 21.5 123.9 19.2 128.6 C 18.9 128.8 19 128 19.1 128.1 C 18.7 128.5 18.9 128.4 18.9 129 C 18.2 127.5 18.4 127.8 19.5 126.5 C 15.3 128.1 20.5 129.7 22.3 129.9 C 24 130.1 25.6 129.7 27.5 129.6 C 29.8 129.4 31 131.1 33 130.5 C 34.1 130.1 35.8 128.1 35.7 127 C 35.1 129.2 33.5 129.3 32.5 127.4 C 32.4 127.6 32.6 127.7 32.6 128.1 C 30.3 127.6 30.2 126.8 32.5 126.6Z').attr({'fill':'#f5f5f5','stroke':'#7d8ea5','stroke-width':'1.5','stroke-opacity':'1'}).data('href','/cartographie/?dep=13'));

mapSet.attr({transform: ['t',5,5]});
mapSet.attr({'cursor':'pointer'}).glow({ color: '#cdcdcd', width:10, offsety:3 }).toBack();
for (var i = 0; i < mapSet.length; i++) {
    var currentSet = mapSet[i];

    if(currentSet.type == 'set') {
        currentSet.mouseover((function (r) {
            return function (e) { r.forEach(hoverEffect) };
        })(currentSet));

        currentSet.mouseout((function (r) {
            return function (e) { r.forEach(outEffect) };
        })(currentSet));

        currentSet.click((function (r) {
            return function (e) { r.forEach(clickHandler) };
        })(currentSet));
    } else {
        currentSet.mouseover(function (e) {
            hoverEffect(this);
        });

        currentSet.mouseout(function (e) {
            outEffect(this);
        });

        currentSet.click(function (e) {
            clickHandler(this);
        });
    }
};

function hoverEffect(element) {
    element.ofill = element.attr('fill');
    element.attr({fill:'#a8c7e6'});
}

function outEffect(element) {
    element.attr({fill:element.ofill});
}

function clickHandler(element) {
    var href = element.data('href');

    if (href == undefined) {
        return;
    };

    window.location = element.data('href');
}