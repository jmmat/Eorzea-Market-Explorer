const expandButton = document.getElementById("expand-history-results");

if(expandButton){
    expandButton.addEventListener("click", function() {
        fetch("/expand-results").then(response => response.text()).then(data => {console.log(data)})
        const saleHistory = document.querySelector(".sale-history-section")
        const item = saleHistory.dataset.item;
        const world = saleHistory.dataset.world;
        console.log(item, world)
    });
}