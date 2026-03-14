const imageInput = document.getElementById("imageInput");
const uploadBtn = document.getElementById("uploadBtn");
const resultBox = document.getElementById("result");
const preview = document.getElementById("preview");
const loading = document.getElementById("loading");

const textInput = document.getElementById("textInput");
const textBtn = document.getElementById("textBtn");

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    preview.style.display = "block";
  };
  reader.readAsDataURL(file);
});


uploadBtn.addEventListener("click", async () => {
  const file = imageInput.files[0];

  if (!file) {
    resultBox.textContent = "Please choose an image first.";
    return;
  }

  const formData = new FormData();
  formData.append("image", file);

  loading.textContent = "Analyzing...";
  resultBox.textContent = "";

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    resultBox.textContent = JSON.stringify(data, null, 2);

  } catch (err) {
    resultBox.textContent = "Error: " + err.message;
  } finally {
    loading.textContent = "";
  }
});


textBtn.addEventListener("click", async () => {

  const text = textInput.value.trim();

  if (!text) {
    resultBox.textContent = "Please enter a product description.";
    return;
  }

  loading.textContent = "Analyzing...";
  resultBox.textContent = "";

  try {
    const res = await fetch("/check-text", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text })
    });

    const data = await res.json();
    resultBox.textContent = JSON.stringify(data, null, 2);

  } catch (err) {
    resultBox.textContent = "Error: " + err.message;
  } finally {
    loading.textContent = "";
  }

});