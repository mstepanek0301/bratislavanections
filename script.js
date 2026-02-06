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
var puzzleNumber = document.getElementById("puzzle-number").innerHTML;
var attemptCount = 0;
var attempts = {};

var selectedTileCount = 0;
var solvedDistrictCount = 0;
var foundGroup = null;
var submitButton = document.getElementById("submit");
var districtForm = document.getElementById("district-form");
var attemptCounter = document.getElementById("attempt-counter");

function updateAttemptCount() {
	attemptCount++;
	attemptCounter.innerHTML = attemptCount.toString() + " " + (
		attemptCount === 1 ? "pokus" :
		attemptCount < 5 ? "pokusy" :
		"pokusov"
	)
}

function handleInput(event) {
	if (foundGroup !== null) {
		foundGroup = null;
		districtForm.style = "display: none";
		submitButton.style = "display: inline-block";
	}
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

function alertAlreadyTried(message, wasTried) {
	if (wasTried) alert("Túto kombináciu si už skúšal(a). " + message);
	else alert(message);
}

function handleSubmit(form) {
	var selectedTiles = [];
	var selectedMask = 0;
	for (var i = 0; i < form.length; i++) {
		var elem = form.elements[i];
		if (elem.checked) {
			var tileNumber = parseInt(elem.name)
			selectedTiles.push(tileNumber);
			selectedMask |= 1 << tileNumber;
		}
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
		foundGroup = puzzleGroups[selectedTiles[0]];
		districtForm.style = "display: block";
		submitButton.style = "display: none";
	}
	else {
		var alreadyTried = attempts[selectedMask];
		if (!alreadyTried) updateAttemptCount();
		if (maxGroupCount === 1) alertAlreadyTried("Žiadne z týchto miest nie sú spolu.", alreadyTried);
		else alertAlreadyTried("O " + (4 - maxGroupCount).toString() + " vedľa!", alreadyTried);
		attempts[selectedMask] = true;
	}
}

function handleDistrictSubmit(form) {
	var selectedMask = foundGroup.toString() + form.elements["district"].value;
	var alreadyTried = attempts[selectedMask];
	if (!alreadyTried) {
		updateAttemptCount();
		attempts[selectedMask] = true;
	}
	if (form.elements["district"].value === puzzleDistricts[foundGroup]) {
		var solvedContainer = document.getElementById("solved");
		var solvedContent = [
			"<p>", districts[puzzleDistricts[foundGroup]], " (",
			difficulties[foundGroup], ")</p>"
		];
		for (var tile = 0; tile < 16; tile++) {
			if (puzzleGroups[tile] !== foundGroup) continue;
			document.getElementById("tile-" + tile.toString()).remove();
			solvedContent.push('<div class="tile"><img src="');
			solvedContent.push(puzzleNumber);
			solvedContent.push('/');
			solvedContent.push(toTwoDigits(tile + 1));
			solvedContent.push('_thumb.jpg"><div class="tile-buttons"><a target="blank" href="');
			solvedContent.push(puzzleNumber);
			solvedContent.push('/');
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
		districtForm.style = "display: none";
		if (++solvedDistrictCount === 4) {
			alert("Gratulujeme!");
		}
		else {
			submitButton.disabled = true;
			submitButton.style = "display: inline-block";
		}
	}
	else {
		alertAlreadyTried("Nesprávna mestská časť.", alreadyTried);
	}
}