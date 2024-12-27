  function cancelOrder(orderId) {
        if (confirm("Bạn có muốn hủy đơn hàng?")) {
            fetch(`/cancel_order`, {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
    },
    body: JSON.stringify({ order_id: orderId }),
})
.then(response => {
    return response.json(); // Chuyển đổi phản hồi thành JSON
})
.then(data => {
    if (data.message) {
        toastr.success(data.message);
        const cancelButton = document.querySelector(`button[onclick="cancelOrder(${orderId})"]`);
        if (cancelButton) {
                 cancelButton.disabled = true;
        }
    } else if (data.error) {
        toastr.error(data.error);
    }
})
.catch(error => {
    console.error("Error:", error);
    toastr.error("Đã xảy ra lỗi, vui lòng thử lại.");
});
        }
    }