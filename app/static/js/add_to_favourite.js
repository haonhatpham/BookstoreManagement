document.getElementById('favorite-form').addEventListener('submit', function(e) {
    e.preventDefault();

    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message); // Thông báo thành công
        } else if (data.error) {
            alert(data.error); // Hiển thị lỗi
        }
    })
    .catch(error => console.error('Error:', error));
});