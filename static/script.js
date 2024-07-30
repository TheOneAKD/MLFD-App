const hamburgerMenu = document.getElementById('hamburgerMenu');
const sidebar = document.getElementById('sidebar');
const addItemOption = document.getElementById('addItemOption');
const removeItemOption = document.getElementById('removeItemOption');
const moveItemOption = document.getElementById('moveItemOption');
const closeAddItemPopupButton = document.getElementById('closeAddItemPopup');
const closeRemoveItemPopupButton = document.getElementById('closeRemoveItemPopup');
const closeMoveItemPopupButton = document.getElementById('closeMoveItemPopup');
const addItemPopup = document.getElementById('addItemPopup');
const removeItemPopup = document.getElementById('removeItemPopup');
const moveItemPopup = document.getElementById('moveItemPopup');

// Function to toggle the sidebar
function toggleSidebar() {
    sidebar.classList.toggle('show-sidebar');
}

// Event listeners
hamburgerMenu.addEventListener('click', toggleSidebar);
addItemOption.addEventListener('click', () => {
    addItemPopup.style.display = 'block';
    removeItemPopup.style.display = 'none';
    moveItemPopup.style.display = 'none';
    sidebar.classList.remove('show-sidebar');
});
removeItemOption.addEventListener('click', () => {
    removeItemPopup.style.display = 'block';
    addItemPopup.style.display = 'none';
    moveItemPopup.style.display = 'none';
    sidebar.classList.remove('show-sidebar');
});
moveItemOption.addEventListener('click', () => {
    moveItemPopup.style.display = 'block';
    addItemPopup.style.display = 'none';
    removeItemPopup.style.display = 'none';
    sidebar.classList.remove('show-sidebar');
});

closeAddItemPopupButton.addEventListener('click', () => {
    addItemPopup.style.display = 'none';
});
closeRemoveItemPopupButton.addEventListener('click', () => {
    removeItemPopup.style.display = 'none';
});
closeMoveItemPopupButton.addEventListener('click', () => {
    moveItemPopup.style.display = 'none';
});

document.addEventListener('click', (event) => {
    if (!sidebar.contains(event.target) && !hamburgerMenu.contains(event.target)) {
        sidebar.classList.remove('show-sidebar');
    }
});

// Function to fetch checklist items data from the server
function fetchChecklistItems() {
    fetch('/get_checklist_items')
        .then(response => response.json())
        .then(data => {
            // Update the checklistItems with the fetched data
            checklistItems = data.checklist_items;
            console.log(checklistItems);  // Debug output

            // You can use this updated data as needed
        })
        .catch(error => {
            console.error('Error fetching checklist items:', error);
        });
}

// Fetch data initially when the page loads
fetchChecklistItems();

// Fetch data every 1 second (adjust the interval as needed)
setInterval(fetchChecklistItems, 1000);  // 1000 milliseconds (1 second)

// ... (the rest of your JavaScript code) ...

function updateCheckbox(section, item_name, checked) {
    // Send an AJAX request to update the checkbox state
    console.log(section);
    console.log(item_name);
    console.log(checked);

    fetch('/update_checkbox', {
        method: 'POST',
        body: JSON.stringify({
            section: section,
            item_name: item_name,
            checked: checked
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response if needed
        console.log(data.message);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


function updateQuantity(section, item_name, newQuantity) {
    // Send an AJAX request to update the item's quantity
    console.log(section);
    console.log(item_name);
    console.log(newQuantity);

    // Update the displayed quantity on the page
    const quantityInput = document.getElementById(`user_quantity_${section}_${item_name}`);
    quantityInput.value = newQuantity;

    fetch('/update_quantity', {
        method: 'POST',
        body: JSON.stringify({
            section: section,
            item_name: item_name,
            new_quantity: newQuantity
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response if needed
        console.log(data.message);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Function to update items dropdown based on the selected section
function updateItemsToRemove() {
    const sectionSelect = document.getElementById('remove_section');
    const itemsSelect = document.getElementById('item_to_remove');
    const selectedSection = sectionSelect.value;
    
    // Clear current items
    itemsSelect.innerHTML = '<option value="" disabled selected>Select Item to Remove</option>';
    
    // Get checklist items from Flask template
    const checklistItems = {{ checklist_items | tojson }};
    
    // Populate items based on the selected section
    if (selectedSection in checklistItems) {
        const items = checklistItems[selectedSection];
        for (const item of items) {
            const option = document.createElement('option');
            option.value = item.item_name;
            option.textContent = item.item_name;
            itemsSelect.appendChild(option);
        }
    }
}

function updateItemsToMove() {
    const previousCategorySelect = document.getElementById('previous_category');
    const itemsSelect = document.getElementById('item_to_move');
    const newCategorySelect = document.getElementById('new_category');
    const selectedSection = previousCategorySelect.value;

    // Clear current items and new category options
    itemsSelect.innerHTML = '<option value="" disabled selected>Select Item to Move</option>';
    newCategorySelect.innerHTML = '<option value="" disabled selected>Select New Section</option>';

    // Get checklist items from Flask template
    const checklistItems = {{ checklist_items | tojson }};
    
    // Populate items based on the selected section
    if (selectedSection in checklistItems) {
        const items = checklistItems[selectedSection];
        for (const item of items) {
            const option = document.createElement('option');
            option.value = item.item_name;
            option.textContent = item.item_name;
            itemsSelect.appendChild(option);
        }
    }

    // Populate new category options excluding the selected previous section
    for (const section in checklistItems) {
        if (section !== selectedSection) {
            const option = document.createElement('option');
            option.value = section;
            option.textContent = section;
            newCategorySelect.appendChild(option);
        }
    }
}

// TXT VERSION

// function generateEngineeringSheettxt() {
//     const name = document.getElementById('name').value;
//     const date = document.getElementById('date').value;
//     const repairOrders = document.getElementById('repair_orders').value;

//     fetch('/get_checklist_items')
//         .then(response => response.json())
//         .then(data => {
//             const checklistItems = data.checklist_items;
//             let engineeringSheetData = `Name: ${name}\nDate: ${date}\nRepair Orders:\n${repairOrders}\n\nSheet:\n`;

//             for (const section in checklistItems) {
//                 engineeringSheetData += `${section}:\n`;
//                 for (const item of checklistItems[section]) {
//                     if (item.checked) {
//                         engineeringSheetData += `√ -- ${item.user_quantity}/${item.correct_quantity} : ${item.item_name}\n`;
//                     } else {
//                         engineeringSheetData += `× -- ${item.user_quantity}/${item.correct_quantity} : ${item.item_name}\n`;
//                     }
//                 }
//             }

//             const blob = new Blob([engineeringSheetData], { type: 'text/plain' });
//             const url = URL.createObjectURL(blob);
//             const a = document.createElement('a');
//             a.href = url;
//             a.download = 'engineering_sheet_' + name + '_' + date + '.txt';
//             document.body.appendChild(a);
//             a.click();
//             window.URL.revokeObjectURL(url);
//         })
//         .catch(error => {
//             console.error('Error fetching checklist items:', error);
//         });
// }

// PDF VERSION

function generateEngineeringSheet() {
    const name = document.getElementById('name').value;
    const date = document.getElementById('date').value;
    const repairOrders = document.getElementById('repair_orders').value;

    const engineeringSheetData = {
        name: name,
        date: date,
        repairOrders: repairOrders,
        checklistItems: {}
    };

    function populateChecklistItems() {
        {% for section, items in session['checklist_items'].items() %}
            engineeringSheetData.checklistItems["{{ section }}"] = [
                {% for item in items %}
                    {
                        item_name: "{{ item.item_name }}",
                        user_quantity: "{{ item.user_quantity }}",
                        correct_quantity: "{{ item.correct_quantity }}",
                        checked: "{{ item.checked }}"
                    },
                {% endfor %}
            ];
        {% endfor %}
    }

    populateChecklistItems();

    fetch('/generate_pdf', {
        method: 'POST',
        body: JSON.stringify(engineeringSheetData),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `engineering_sheet_${date}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error generating PDF:', error);
    });
}
