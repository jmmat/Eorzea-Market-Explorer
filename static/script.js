/*
 * Fetches and updates market content dynamically without
 * reloading the entire webpage.
 */

// Keep the page's static elements alive while
// search and random results are requested from Flask.
const marketSelector = ".market-content";
let activeMarketRequest = null;

// Manually save the market panel so the Back button can restore it without a reload.
const initialMarket = document.querySelector(marketSelector);
if (initialMarket) {
    history.replaceState(
        { ...history.state, emeMarketHtml: initialMarket.outerHTML },
        "",
        window.location.href
    );
}

function setMarketLoading(loading, message = "") {
    const market = document.querySelector(marketSelector);
    const status = market?.querySelector(".request-status");
    const submitButton = market?.querySelector("#submit-button");
    const randomButton = document.getElementById("random-item-button");

    if (market) {
        market.setAttribute("aria-busy", String(loading));
    }
    if (status) {
        status.textContent = message;
    }
    if (submitButton) {
        submitButton.disabled = loading;
    }
    if (randomButton) {
        randomButton.disabled = loading;
    }
}

function marketNodeFromHtml(html) {
    const page = new DOMParser().parseFromString(html, "text/html");
    const market = page.querySelector(marketSelector);
    if (!market) {
        throw new Error("The server did not return the market content.");
    }
    return market;
}

// Avoids recreating the entire page, preserving the header, background, and other static elements
function replaceMarket(market) {
    const currentMarket = document.querySelector(marketSelector);
    if (!currentMarket) {
        throw new Error("The current market content is missing.");
    }
    currentMarket.replaceWith(market); 
}

async function loadMarket(url, addHistory = true) {
    if (activeMarketRequest) {
        activeMarketRequest.abort();
    }

    const controller = new AbortController();
    const fetchOptions = {
        cache: "no-store", // Prevent the browser from reusing a cached response
        headers: { "EME-Partial": "1" },
        signal: controller.signal
    };

    activeMarketRequest = controller;
    setMarketLoading(true, "Loading market data…");

    try {
        const response = await fetch(url, fetchOptions);  // Fetch the HTML market data from Flask
        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}.`);
        }

        const html = await response.text();
        if (controller.signal.aborted) {
            return;
        }

        const newMarket = marketNodeFromHtml(html);
        const marketSnapshot = newMarket.outerHTML; // Store the HTML snapshot for manual history management
        replaceMarket(newMarket);

        if (addHistory) {
            history.pushState({ emeMarketHtml: marketSnapshot }, "", url);
        } else {
            history.replaceState({ emeMarketHtml: marketSnapshot }, "", url);
        }
    } catch (error) {
        if (error.name !== "AbortError") {
            console.error("Market request failed:", error);
            setMarketLoading(false, "Couldn't load the results. Please try again.");
        }
    } finally {
        if (activeMarketRequest === controller) { // Reset the UI after the request completes or is aborted
            activeMarketRequest = null;
            const status = document.querySelector(".request-status");
            if (status?.textContent === "Loading market data…") {
                status.textContent = "";
            }
            setMarketLoading(false, status?.textContent || "");  // Set the loading state to false and update the status message
        }
    }
}

// Listen on document because the search form is replaced after each request
document.addEventListener("submit", (event) => {
    const form = event.target.closest(".search-form");
    if (!form) {
        return;
    }
    event.preventDefault(); // Handle submission with JavaScript instead of the default form submission

    const url = new URL(form.action, window.location.href);
    url.search = new URLSearchParams(new FormData(form)).toString();
    loadMarket(url.href); // Load the market data for the given URL
});

document.addEventListener("click", (event) => {
    const randomButton = event.target.closest("#random-item-button");
    if (randomButton) {
        event.preventDefault(); // Allow Javascript to handle the button click instead of the default action
        loadMarket(new URL("/random", window.location.origin).href);
        return;
    }

    const expandButton = event.target.closest("#expand-history-results");
    if (expandButton) {
        event.preventDefault(); // Allow Javascript to handle the button click instead of the default action
        toggleHistory(expandButton);
    }
});

async function toggleHistory(button) {
    const saleHistory = button.closest(".sale-history-section");
    const saleHistoryBody = saleHistory?.querySelector("#sale-history-body");
    const errorMessage = saleHistory?.querySelector("#expanded-search-error-message");
    if (!saleHistoryBody || !errorMessage || button.disabled) {
        return;
    }

    if (button.dataset.expanded === "true") {
        saleHistoryBody.querySelectorAll(".expanded-row").forEach(row => row.remove());
        button.textContent = "▼ Expand Results";
        button.dataset.expanded = "false";
        errorMessage.textContent = "";
        return;
    }

    const originalRowCount = saleHistoryBody.rows.length;
    const query = new URLSearchParams({
        item_id: saleHistory.dataset.itemId,
        world: saleHistory.dataset.world
    });

    button.disabled = true;
    errorMessage.textContent = "";
    try {
        const response = await fetch(`/expand-results?${query}`);
        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}.`);
        }
        const data = await response.json();

        if (data.timeout) {
            throw new Error("Server timed out. Try again in a moment.");
        }
        if (data.error) {
            throw new Error(`Unable to retrieve results. Status ${data.status_code}.`);
        }
        if (!Array.isArray(data.recentHistory)) {
            throw new Error("Invalid sale history response.");
        }

        // Prevent updating old sale history if a new search has already finished
        if (!saleHistory.isConnected) {
            return;
        }

        const fields = ["pricePerUnit", "quantity", "hq", "timestamp", "buyerName"];
        if (["Aether", "Primal", "Crystal", "Dynamis"].includes(saleHistory.dataset.world)) {
            fields.push("worldName");
        }

        for (const purchase of data.recentHistory.slice(originalRowCount)) {
            const row = document.createElement("tr");
            row.classList.add("expanded-row");
            for (const field of fields) {
                const cell = document.createElement("td");
                cell.textContent = purchase[field] ?? ""; // Fill the cell with the value, or leave it empty if null or undefined
                row.appendChild(cell);
            }
            saleHistoryBody.appendChild(row);
        }
        button.textContent = "▲ Collapse Results";
        button.dataset.expanded = "true";
    } catch (error) {
        if (saleHistory.isConnected) {
            errorMessage.textContent = error.message;
        }
        console.error("Expanded history request failed:", error);
    } finally {
        if (saleHistory.isConnected) {
            button.disabled = false;
        }
    }
}

window.addEventListener("popstate", (event) => {
    if (activeMarketRequest) {
        activeMarketRequest.abort();
        activeMarketRequest = null;
    }

    if (event.state?.emeMarketHtml) {
        replaceMarket(marketNodeFromHtml(event.state.emeMarketHtml));
        setMarketLoading(false);
    } else {
        // Fallback for a history entry without a saved snapshot.
        loadMarket(window.location.href, false);
    }
});
