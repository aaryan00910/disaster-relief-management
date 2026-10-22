function dismissAlert(button) {
    const alert = button.closest('.flash-alert');
    if (alert) {
        alert.remove();
    }
}

function populateEditInventory(id, name, category, quantity, unit, threshold, location) {
    const form = document.getElementById('editInventoryForm');

    if (!form) {
        console.error('Edit inventory form not found.');
        return;
    }

    form.action = `/inventory/edit/${id}`;

    document.getElementById('edit_inv_name').value = name;
    document.getElementById('edit_inv_category').value = category;
    document.getElementById('edit_inv_quantity').value = quantity;
    document.getElementById('edit_inv_unit').value = unit;
    document.getElementById('edit_inv_threshold').value = threshold;
    document.getElementById('edit_inv_location').value = location;

    if (typeof openModal === 'function') {
        openModal('editInventoryModal');
    } else {
        document.getElementById('editInventoryModal').style.display = 'flex';
    }
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);

    if (!modal) {
        console.error("Modal not found:", modalId);
        return;
    }

    modal.style.display = "flex";
    modal.classList.add("active");
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);

    if (!modal) {
        console.error("Modal not found:", modalId);
        return;
    }

    modal.style.display = "none";
    modal.classList.remove("active");
}


