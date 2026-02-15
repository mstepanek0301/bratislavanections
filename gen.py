from streetlevel import streetview
from PIL import Image
import numpy
from scipy.ndimage import map_coordinates
import sys
import json
import random
import unicodedata

copyrights = set()

def normalize(s):
	return "".join((c for c in unicodedata.normalize("NFD", s.lower()) if c.isalpha()))

def interpolate_colors(array, coords):
	red = map_coordinates(array[:, :, 0], coords, order = 1, mode = "wrap")
	green = map_coordinates(array[:, :, 1], coords, order = 1, mode = "wrap")
	blue = map_coordinates(array[:, :, 2], coords, order = 1, mode = "wrap")
	return numpy.stack((red, green, blue), axis = -1)

def image_from_panorama(panorama, dest, width, height, field_of_view, yaw, pitch):
	pano_array = numpy.array(panorama)
	pano_width, pano_height = panorama.size
	yaw_radians = numpy.radians(yaw)
	pitch_radians = numpy.radians(pitch)

	two_pi = 2 * numpy.pi
	pi_half = numpy.pi / 2

	sin_pitch = numpy.sin(pitch_radians)
	cos_pitch = numpy.cos(pitch_radians)

	focal_length = width / numpy.tan(numpy.radians(field_of_view) / 2) / 2

	u, v = numpy.meshgrid(numpy.arange(width), numpy.arange(height), indexing = "xy")

	# coordinates of the screen in space
	x = u - width / 2
	y = v - height / 2
	z = focal_length

	distance = numpy.sqrt(x ** 2 + y ** 2 + z ** 2)

	# pitched screen
	pitched_x = x
	pitched_y = y * cos_pitch - z * sin_pitch
	pitched_z = y * sin_pitch + z * cos_pitch

	# spherical coordinates
	lat = numpy.arcsin(pitched_y / distance) + pi_half
	lon = (numpy.arctan2(pitched_x, pitched_z) + yaw_radians) % two_pi

	# coordinates in the panorama
	U = pano_height * lon / numpy.pi
	V = pano_width * lat / two_pi

	colors = interpolate_colors(pano_array, numpy.vstack((V.flatten(), U.flatten())))
	image = Image.fromarray(colors.reshape((height, width, 3)), "RGB")
	image.save(dest)

def apply_pitch(x, y, z, angle):
	return x, y * numpy.cos(angle) - z * numpy.sin(angle), z * numpy.cos(angle) + y * numpy.sin(angle)

def apply_roll(x, y, z, angle):
	return x * numpy.cos(angle) - y * numpy.sin(angle), y * numpy.cos(angle) + x * numpy.sin(angle), z

def apply_yaw(x, y, z, angle):
	return x * numpy.cos(angle) + z * numpy.sin(angle), y, z * numpy.cos(angle) - x * numpy.sin(angle)

# all the angles are in radians
def image_from_panorama_correct(pano, dest, width, height, fov, yaw, pitch, pano_yaw, pano_pitch, pano_roll):
	pano_array = numpy.array(pano)
	pano_width, pano_height = pano.size

	focal_length = width / numpy.tan(fov / 2) / 2

	u, v = numpy.meshgrid(numpy.arange(width), numpy.arange(height), indexing = "xy")

	# coordinates of the screen in space
	x = u - width / 2
	y = v - height / 2
	z = focal_length

	distance = numpy.sqrt(x ** 2 + y ** 2 + z ** 2)

	# corrections
	x, y, z = apply_pitch(x, y, z, pitch)
	x, y, z = apply_yaw(x, y, z, yaw - pano_yaw)
	x, y, z = apply_pitch(x, y, z, pano_pitch)
	x, y, z = apply_roll(x, y, z, -pano_roll)

	# spherical coordinates
	lat = numpy.arcsin(y / distance) + numpy.pi / 2
	lon = (numpy.arctan2(x, z) + numpy.pi) % (2 * numpy.pi)

	# coordinates in the panorama
	U = pano_height * lon / numpy.pi
	V = pano_width * lat / 2 / numpy.pi

	colors = interpolate_colors(pano_array, numpy.vstack((V.flatten(), U.flatten())))
	image = Image.fromarray(colors.reshape((height, width, 3)), "RGB")
	image.save(dest)

def generate_image(pano_id, dest, heading, pitch):
	pano = streetview.find_panorama_by_id(pano_id)
	print("downloading image for", dest)
	pano_image = streetview.get_panorama(pano, 3)
	#pano_image = Image.open(f"pano-cache/{dest}")
	#pano_image.save(f"pano-cache/{dest}")
	print("processing image for", dest)
	image_from_panorama_correct(
		pano_image, dest, 1920, 1200, numpy.radians(120),
		numpy.radians(heading), numpy.radians(pitch), pano.heading, pano.pitch, pano.roll,
	)
	copyrights.add(pano.copyright_message)

def twodigit(n):
	alphabet = "0123456789"
	return alphabet[n // 10] + alphabet[n % 10]

puzzle = sys.argv[1]
puzzle_file = open(f"{puzzle}/puzzle.json")
puzzle_data = json.loads(puzzle_file.read())
puzzle_file.close()

random.seed(421 + int(puzzle))

locations = puzzle_data["customCoordinates"]
random.shuffle(locations)

difficulties = []
districts = ["", "", "", ""]
google_maps_ids = []

for i, location in enumerate(locations):
	pano_id = location["panoId"]
	if pano_id is None: pano_id = location["extra"]["panoId"]
	generate_image(pano_id, f"{puzzle}/{twodigit(i + 1)}.jpg", location["heading"], location["pitch"])
	district, difficulty_name = location["extra"]["tags"][0].split()
	difficulty = ["lahke", "stredne", "tazke", "expert"].index(normalize(difficulty_name))
	if districts[difficulty]: assert districts[difficulty] == district
	else: districts[difficulty] = district
	difficulties.append(difficulty)
	google_maps_ids.append(streetview.build_permalink(
		id = pano_id,
		lon = location["lng"], lat = location["lat"],
		heading = location["heading"], pitch = location["pitch"] + 90,
	))

for i in range(4):
	assert difficulties.count(i) == 4

outfile = open("index.html", "w")
print(f"""\
<!DOCTYPE HTML>
<html lang="sk">
<head>
	<title>Bratislavanections</title>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="stylesheet" href="style.css">
</head>
<body onclick="">
	<h1><span class="highlight">Bratislava</span>nections</h1>
	<p>
		Tieto fotky sú zo 4 mestských častí Bratislavy a z každej mestskej časti sú 4 fotky.
		Tvojou úlohou je označiť tieto štvorice a priradiť ich k mestským častiam.
		Fotky sú z Google Street View.
	</p>
	<p><a href="{int(puzzle) - 1}">&larr;</a> číslo <span id="puzzle-number">{puzzle}</span></p>
	<p><b>Nové číslo každý pondelok!</b> <a href="navrhni">Navrhni vlastné</a></p>
	<p id="attempt-counter">0 pokusov</p>
	<form id="district-form" action="javascript:0;" onsubmit="handleDistrictSubmit(this)">
	   <label>
			Ktorá je to mestská časť?
			<select id="district">
				<option value="cu">Čunovo</option>
				<option value="de">Devín</option>
				<option value="dv">Devínska Nová Ves</option>
				<option value="du">Dúbravka</option>
				<option value="ja">Jarovce</option>
				<option value="kv">Karlova Ves</option>
				<option value="la">Lamač</option>
				<option value="nm">Nové Mesto</option>
				<option value="pe">Petržalka</option>
				<option value="pb">Podunajské Biskupice</option>
				<option value="ra">Rača</option>
				<option value="rs">Rusovce</option>
				<option value="ru">Ružinov</option>
				<option value="sm">Staré Mesto</option>
				<option value="va">Vajnory</option>
				<option value="vr">Vrakuňa</option>
				<option value="zb">Záhorská Bystrica</option>
			</select>
		</label>
		<input type="submit" value="Hádaj">
	</form>
	<form action="javascript:0;" onsubmit="handleSubmit(this)" oninput="handleInput(event)">
		<input type="submit" value="Hádaj" id="submit" disabled>
		<div id="solved">
		</div>
		<div id="tiles">
			<label class="tile" id="tile-0">
				<input name="0" type="checkbox">
				<img src="{puzzle}/01_thumb.jpg">
				<a target="blank" href="{puzzle}/01.jpg">↗</a>
			</label><label class="tile" id="tile-1">
				<input name="1" type="checkbox">
				<img src="{puzzle}/02_thumb.jpg">
				<a target="blank" href="{puzzle}/02.jpg">↗</a>
			</label><label class="tile" id="tile-2">
				<input name="2" type="checkbox">
				<img src="{puzzle}/03_thumb.jpg">
				<a target="blank" href="{puzzle}/03.jpg">↗</a>
			</label><label class="tile" id="tile-3">
				<input name="3" type="checkbox">
				<img src="{puzzle}/04_thumb.jpg">
				<a target="blank" href="{puzzle}/04.jpg">↗</a>
			</label><label class="tile" id="tile-4">
				<input name="4" type="checkbox">
				<img src="{puzzle}/05_thumb.jpg">
				<a target="blank" href="{puzzle}/05.jpg">↗</a>
			</label><label class="tile" id="tile-5">
				<input name="5" type="checkbox">
				<img src="{puzzle}/06_thumb.jpg">
				<a target="blank" href="{puzzle}/06.jpg">↗</a>
			</label><label class="tile" id="tile-6">
				<input name="6" type="checkbox">
				<img src="{puzzle}/07_thumb.jpg">
				<a target="blank" href="{puzzle}/07.jpg">↗</a>
			</label><label class="tile" id="tile-7">
				<input name="7" type="checkbox">
				<img src="{puzzle}/08_thumb.jpg">
				<a target="blank" href="{puzzle}/08.jpg">↗</a>
			</label><label class="tile" id="tile-8">
				<input name="8" type="checkbox">
				<img src="{puzzle}/09_thumb.jpg">
				<a target="blank" href="{puzzle}/09.jpg">↗</a>
			</label><label class="tile" id="tile-9">
				<input name="9" type="checkbox">
				<img src="{puzzle}/10_thumb.jpg">
				<a target="blank" href="{puzzle}/10.jpg">↗</a>
			</label><label class="tile" id="tile-10">
				<input name="10" type="checkbox">
				<img src="{puzzle}/11_thumb.jpg">
				<a target="blank" href="{puzzle}/11.jpg">↗</a>
			</label><label class="tile" id="tile-11">
				<input name="11" type="checkbox">
				<img src="{puzzle}/12_thumb.jpg">
				<a target="blank" href="{puzzle}/12.jpg">↗</a>
			</label><label class="tile" id="tile-12">
				<input name="12" type="checkbox">
				<img src="{puzzle}/13_thumb.jpg">
				<a target="blank" href="{puzzle}/13.jpg">↗</a>
			</label><label class="tile" id="tile-13">
				<input name="13" type="checkbox">
				<img src="{puzzle}/14_thumb.jpg">
				<a target="blank" href="{puzzle}/14.jpg">↗</a>
			</label><label class="tile" id="tile-14">
				<input name="14" type="checkbox">
				<img src="{puzzle}/15_thumb.jpg">
				<a target="blank" href="{puzzle}/15.jpg">↗</a>
			</label><label class="tile" id="tile-15">
				<input name="15" type="checkbox">
				<img src="{puzzle}/16_thumb.jpg">
				<a target="blank" href="{puzzle}/16.jpg">↗</a>
			</label>
		</div>
		<p><small>Fotky {", ".join(copyrights)}</small></p>
	</form>
</body>
<script>
	// [id] -> difficulty (0 = easy, 3 = hard)
	var puzzleGroups = {repr(difficulties)};
	// [difficulty] -> district (2-letter string)
	var puzzleDistricts = {repr(districts)};
	var googleMapsIds = {repr(google_maps_ids)};
</script>
<script src="script.js"></script>
</html>
""", file = outfile)
outfile.close()