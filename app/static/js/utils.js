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

function handleAddSummaryForm(event) {
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
  let sources_string = JSON.stringify(sources);

  let submitURL = document.getElementById("submit-url").value;

  let submitButton = document.getElementById("submit-button");
  submitButton.disabled = true;
  submitButton.innerHTML = "Submitting...";

  fetch(submitURL, {
    method: "POST",
    body: JSON.stringify({
      summary: summary,
      sources: sources_string,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
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

if (document.getElementById("add-form-summary")) {
  document
    .getElementById("add-form-summary")
    .addEventListener("submit", handleAddSummaryForm);
}

function handleAddFamousPeopleSummaryForm(event) {
  event.preventDefault();
  let summary = document.getElementById("summary").value;
  if (summary == "") {
    alert("Summary cannot be empty.");
    return false;
  }

  let name = document.getElementById("name").value;
  if (name == "") {
    alert("Name cannot be empty.");
    return false;
  }
  
  let lifetime = document.getElementById("lifetime").value;
  if (lifetime == "") {
    alert("Lifetime cannot be empty.");
    return false;
  }
  
  // Get the file uploaded
  let image = document.getElementById("image").files[0];
  if (image == undefined) {
    alert("A image is required to be uploaded.");
    return false;
  }

  let formData = new FormData();
  formData.append("summary", summary);
  formData.append("name", name);
  formData.append("lifetime", lifetime);
  formData.append("image", image);
  formData.append("century", document.getElementById("century").value);
  formData.append("decade", document.getElementById("decade").value);
  formData.append("year", document.getElementById("year").value);

  let submitURL = document.getElementById("submit-url").value;

  let submitButton = document.getElementById("submit-button");
  submitButton.disabled = true;
  submitButton.innerHTML = "Submitting...";
  fetch(submitURL, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data["status"] == "success") {
        alert(data["message"]);
        window,location.href = data["redirect"];
      } else {
        alert(data["message"]);
        submitButton.disabled = false;
        submitButton.innerHTML = "Submit";
        return;
      }
    });
}

if (document.getElementById("add-form-famous-pople-summary")) {
  document
    .getElementById("add-form-famous-pople-summary")
    .addEventListener("submit", handleAddFamousPeopleSummaryForm);
}


function handleSummaryForm(event) {
  event.preventDefault();
  let summary = document.getElementById("summary").value;
  if (summary == "") {
    alert("Summary cannot be empty.");
    return false;
  }
  let originalSummary = document.getElementById("default-summary").textContent;

  if (summary == originalSummary) {
    alert("Edited summary cannot be the same as the original summary.");
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
  let sources_string = JSON.stringify(sources);

  let submitURL = document.getElementById("submit-url").value;

  let submitButton = document.getElementById("submit-button");
  submitButton.disabled = true;
  submitButton.innerHTML = "Submitting...";

  fetch(submitURL, {
    method: "POST",
    body: JSON.stringify({
      summary: summary,
      sources: sources_string,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
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

if (document.getElementById("edit-form-summary")) {
  document
    .getElementById("edit-form-summary")
    .addEventListener("submit", handleSummaryForm);
}

function handleFamousPeopleSummaryForm(event) {
  event.preventDefault();
  let summary = document.getElementById("summary").value;
  if (summary == "") {
    alert("Summary cannot be empty.");
    return false;
  }
  let originalSummary = document.getElementById("default-summary").textContent;
  if (summary == originalSummary) {
    alert("Edited summary cannot be the same as the original summary.");
    return false;
  }
  let submitURL = document.getElementById("submit-url").value;

  let submitButton = document.getElementById("submit-button");
  submitButton.disabled = true;
  submitButton.innerHTML = "Submitting...";

  fetch(submitURL, {
    method: "POST",
    body: JSON.stringify({
      summary: summary,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
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

if (document.getElementById("edit-famous-people-form-summary")) {
  document
    .getElementById("edit-famous-people-form-summary")
    .addEventListener("submit", handleFamousPeopleSummaryForm);
}

const items = document.querySelectorAll(".accordion button");

function toggleAccordion() {
  const itemToggle = this.getAttribute("aria-expanded");

  for (i = 0; i < items.length; i++) {
    items[i].setAttribute("aria-expanded", "false");
  }

  if (itemToggle == "false") {
    this.setAttribute("aria-expanded", "true");
  }
}

items.forEach((item) => item.addEventListener("click", toggleAccordion));
