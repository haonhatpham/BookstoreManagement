if (window.location.pathname === '/change_password') {
    // Function to change the password
    async function changePassword(currentPassword, newPassword, newPasswordAgain) {
    try {
        // Validate input fields
        if (!currentPassword || !newPassword || !newPasswordAgain) {
            toastr.error('Vui lòng điền đầy đủ các trường!');
            return;
        }

        if (newPassword !== newPasswordAgain) {
            toastr.error('Mật khẩu mới không khớp!');
            return;
        }

        // Send POST request to the '/change_password' route
        const response = await fetch('/api/change_passwd', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'current_password': currentPassword,
                'new_password': newPassword
            })
        });

        // Parse JSON response
        const data = await response.json();

        // Handle response based on the status code
        if (response.ok) {
            console.log(data.message); // Success message
            toastr.success(data.message);
            document.getElementById('inputCurrentPassword').value = '';
            document.getElementById('inputNewPassword').value = '';
            document.getElementById('inputNewPasswordAgain').value = '';
        } else {
            toastr.error(data.error);
        }
    } catch (error) {
        console.error('Network error:', error);
        alert('Có lỗi xảy ra trong quá trình kết nối!');
    }
    }

    const form = document.querySelector('#form-change-pw');

    form.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent form submission
    const currentPassword = document.getElementById('inputCurrentPassword').value;
    const newPassword = document.getElementById('inputNewPassword').value;
    const newPasswordAgain = document.getElementById('inputNewPasswordAgain').value;

    changePassword(currentPassword, newPassword, newPasswordAgain);
    });
}