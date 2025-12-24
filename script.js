function toTwoDigits(n) {
	return Math.floor(n / 10).toString() + (n % 10).toString()
}

var districts = {};
for (
	var option = document.getElementById("district").firstChild;
	option !== null; option = option.nextSibling
) {
	if (option.value === undefined) continue;
	districts[option.value] = option.innerHTML;
}
var difficulties = ["ľahké", "stredné", "ťažké", "expert"];

var selectedTileCount = 0;
var solvedDistrictCount = 0;
var submitButton = document.getElementById("submit");

function handleInput(event) {
	if (event.target.tagName !== "INPUT") return;
	if (event.target.checked) {
		if (selectedTileCount === 4) event.target.checked = false;
		else selectedTileCount++;
		if (selectedTileCount === 4) submitButton.disabled = false;
	}
	else {
		selectedTileCount--;
		if (selectedTileCount === 3) submitButton.disabled = true;
	}
}

function handleSubmit(form) {
	var selectedTiles = [];
	for (var i = 0; i < form.length; i++) {
		var elem = form.elements[i];
		if (elem.checked) selectedTiles.push(parseInt(elem.name));
	}
	if (selectedTiles.length !== 4) {
		alert("Nesprávny počet vybratých miest, majú byť 4.");
		return;
	}
	var countsByGroup = [0, 0, 0, 0];
	var maxGroupCount = 0;
	for (var i = 0; i < 4; i++) {
		var count = ++countsByGroup[puzzleGroups[selectedTiles[i]]];
		if (count > maxGroupCount) maxGroupCount = count;
	}
	if (maxGroupCount === 4) {
		var selectedDistrict = puzzleDistricts[puzzleGroups[selectedTiles[0]]]
		if (form.elements["district"].value === selectedDistrict) {
			var solvedContainer = document.getElementById("solved");
			var solvedContent = [
				"<p>", districts[selectedDistrict], " (",
				difficulties[puzzleGroups[selectedTiles[0]]], ")</p>"
			];
			for (var i = 0; i < 4; i++) {
				var tile = selectedTiles[i];
				document.getElementById("tile-" + tile.toString()).remove();
				solvedContent.push('<div class="tile"><img src="');
				solvedContent.push(toTwoDigits(tile + 1));
				solvedContent.push('_thumb.jpg"><div class="tile-buttons"><a target="blank" href="');
				solvedContent.push(toTwoDigits(tile + 1));
				solvedContent.push('.jpg">↗</a> <a target="blank" href="https://maps.app.goo.gl/');
				solvedContent.push(googleMapsIds[tile]);
				solvedContent.push('">mapa</a></div></div>');
			}
			var solvedGroup = document.createElement("div");
			solvedGroup.innerHTML = solvedContent.join("");
			solvedGroup.className = "solved-group";
			solvedContainer.appendChild(solvedGroup);
			selectedTileCount = 0;
			submitButton.disabled = true;
			if (++solvedDistrictCount === 4) {
				alert("Gratulujeme!");
			}
		}
		else {
			alert("Tieto 4 miesta sú spolu, ale patria do inej mestskej časti.");
		}
	}
	else {
		if (maxGroupCount === 1) alert("Žiadne z týchto miest nie sú spolu.");
		else alert("O " + (4 - maxGroupCount).toString() + " vedľa!");
	}
}