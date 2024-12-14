if (window.location.pathname === '/manage_info') {
document.querySelector('form').addEventListener('submit', function(event) {
    event.preventDefault(); // Ngừng việc gửi form theo cách thông thường

    // Lấy dữ liệu từ các trường trong form
    const username = document.getElementById('inputUsername').value;
    const name = document.getElementById('inputName').value;
    const email = document.getElementById('inputEmail').value;
    const phoneNumber = document.getElementById('inputPhoneNumber').value;
    const gender = document.querySelector('input[name="radioGender"]:checked').id === 'radioGender1' ? true : false;
    const city = document.getElementById('inputCity').value;
    const district = document.getElementById('inputDistrict').value;
    const ward = document.getElementById('inputWard').value;
    const street = document.getElementById('inputDetailAddress').value;

    // Tạo đối tượng dữ liệu để gửi đi
    const data = {
        username,
        name,
        email,
        phone_number: phoneNumber,
        gender,
        city,
        district,
        ward,
        street
    };

    // Gửi yêu cầu fetch tới server
    fetch('/manage_user_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastr.success("Cập nhật thông tin thành công!");
        } else {
            toastr.error("Có lỗi xảy ra khi cập nhật thông tin.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        toastr.error('Có lỗi xảy ra, vui lòng thử lại.');
    });
});


}