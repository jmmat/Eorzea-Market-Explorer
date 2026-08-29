const expandButton = document.getElementById("expand-history-results");
let expanded = false;

if(expandButton){
    expandButton.addEventListener("click", function() {
        const saleHistory = document.querySelector(".sale-history-section");
        const saleHistoryBody = document.getElementById("sale-history-body");
        const item = saleHistory.dataset.item;
        const item_id = saleHistory.dataset.itemId;
        const world = saleHistory.dataset.world;

        if(!expanded){
            fetch(`/expand-results?item_id=${item_id}&world=${world}`).then(response => response.json()).then(data => {
                if(data.error){
                    const errorMessage = document.getElementById("expanded-search-error-message");
                    errorMessage.textContent = `Unable to retrieve expanded results. Server returned status ${data.status_code}`
                    console.log("Universalis error: ", data.status_code);
                    return;
                }
                if(data.timeout){
                    const timeoutMessage = document.getElementById("expanded-search-error-message");
                    timeoutMessage.textContent = "Server timed out, try again in a second"
                    console.log("Universalis timed out");
                    return;
                }
                console.log(data);

                const fields = ["pricePerUnit", "quantity", "hq", "timestamp", "buyerName"];

                for(let i = 5; i < data["recentHistory"].length; i++) {
                    const row = document.createElement("tr");
                    row.classList.add("expanded-row");

                    for(let field of fields){
                        const cell = document.createElement("td");
                        cell.textContent = data["recentHistory"][i][field];
                        row.appendChild(cell);
                    }

                    saleHistoryBody.appendChild(row);
                }
                expandButton.textContent = "▲ Collapse Results";
                expanded = true;
            });
            console.log(item, world);
        } else {
            const expandedRows = document.querySelectorAll(".expanded-row");

            for(let row of expandedRows){
                row.remove();
            }

            expandButton.textContent = "▼ Expand Results";
            expanded = false;
        }
    });
}