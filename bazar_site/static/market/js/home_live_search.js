document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".home-search-form");
  const input = form ? form.querySelector('input[name="q"]') : null;
  const grid = document.getElementById("home-listings-grid");

  if (!form || !input || !grid) {
    return;
  }

  let lastValue = input.value;
  let debounceTimer = null;
  let currentController = null;

  const runSearch = (value) => {
    const q = value.trim();

    if (currentController) {
      currentController.abort();
    }
    currentController = new AbortController();

    const params = new URLSearchParams();
    if (q) {
      params.set("q", q);
    }

    fetch(form.dataset.liveSearchUrl + "?" + params.toString(), {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      signal: currentController.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        if (typeof data.html === "string") {
          grid.innerHTML = data.html;
        }
      })
      .catch((error) => {
        if (error.name === "AbortError") {
          return;
        }
        console.error("Home live search error:", error);
      });
  };

  const scheduleSearch = () => {
    const value = input.value;
    if (value === lastValue) {
      return;
    }
    lastValue = value;

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(() => runSearch(value), 250);
  };

  input.addEventListener("input", scheduleSearch);

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    scheduleSearch();
  });
});

