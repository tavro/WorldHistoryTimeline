// Get all elements with class people_summary and normalize the text in it to 300 wwords

function normalizeString() {
    var elements = document.getElementsByClassName("people_summary");
    for (var i = 0; i < elements.length; i++) {
        var text = elements[i].innerHTML;
        var normalizedText = text.split(" ").slice(0, 50).join(" ");
        elements[i].innerHTML = `${normalizedText}... <a href="/famous-people/${elements[i].id}">Read more</a>`;
    }
}

normalizeString();