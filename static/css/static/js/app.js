function dismissAlert(button) {
    const alert = button.closest('.flash-alert');
    if (alert) {
        alert.remove();
    }
}
