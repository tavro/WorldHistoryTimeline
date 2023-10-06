function ordinal_suffix_of(i) {
  var j = i % 10,
    k = i % 100;
  if (j == 1 && k != 11) {
    return i + "st";
  }
  if (j == 2 && k != 12) {
    return i + "nd";
  }
  if (j == 3 && k != 13) {
    return i + "rd";
  }
  return i + "th";
}

let elements = document.getElementsByClassName("ordinal_suffix");

for (let i = 0; i < elements.length; i++) {
  elements[i].innerHTML = ordinal_suffix_of(elements[i].innerHTML);
}

function addSource() {
  let source = document.getElementById("source").value;
  if (source == "") {
    return;
  }
  if (!source.includes("http://") && !source.includes("https://")) {
    alert("Please enter a valid source URL.");
    return;
  }

  let sourceList = document.getElementById("source-list");
  let p = document.createElement("p");
  p.innerHTML = source;
  let button = document.createElement("button");
  button.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"/></svg>`;
  button.setAttribute("onclick", "removeSource(this)");
  let li = document.createElement("li");
  li.appendChild(p);
  li.appendChild(button);
  li.setAttribute("data-source", source);
  sourceList.appendChild(li);
  document.getElementById("source").value = "";
}

function removeSource(callingElement) {
  let li = callingElement.parentNode;
  let sourceList = document.getElementById("source-list");
  sourceList.removeChild(li);
}

function handleSummaryForm(event) {
  event.preventDefault();
  let summary = document.getElementById("summary").value;
  if (summary == "") {
    alert("Summary cannot be empty.");
    return false;
  }
  let sourceList = document.getElementById("source-list");
  if (sourceList.children.length == 0) {
    alert("Please add at least one source.");
    return false;
  }
  let sources = [];
  for (let i = 0; i < sourceList.children.length; i++) {
    sources.push(sourceList.children[i].getAttribute("data-source"));
  }
  document.getElementById("source").value = JSON.stringify(sources);
  
  let submitURL = document.getElementById("submit-url").value;
  
  let submitButton = document.getElementById("submit-button");
  submitButton.disabled = true;
  submitButton.innerHTML = "Submitting...";

  let newSources = document.getElementById("source").value;

  fetch(submitURL, {
    method: "POST",
    body: JSON.stringify({
      summary: summary,
      sources: newSources
    }),
    headers: {
      "Content-Type": "application/json"
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data["status"] == "success") {
        alert(data["message"]);
        window.location.href = data["redirect"];
      } else {
        alert(data["message"]);
        submitButton.disabled = false;
        submitButton.innerHTML = "Submit";
      }
    });
}

document.getElementById("edit-form-summary").addEventListener("submit", handleSummaryForm);
